"""HuggingFace dataset backend for asebytes."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterator
from typing import Any

from asebytes._protocols import ReadableBackend
from asebytes.hf._mappings import COLABFIT, OPTIMADE, ColumnMapping


def load_dataset(path: str, *, streaming: bool = False, split: str | None = None, **kwargs):
    """Lazy wrapper around ``datasets.load_dataset``.

    Raises a helpful ImportError if the ``datasets`` library is not installed.
    """
    try:
        from datasets import load_dataset as _hf_load_dataset
    except ImportError:
        raise ImportError(
            "The 'datasets' package is required for the HuggingFace backend. "
            "Install it with: pip install datasets"
        ) from None
    return _hf_load_dataset(path, streaming=streaming, split=split, **kwargs)


class HuggingFaceBackend(ReadableBackend):
    """Read-only backend for HuggingFace datasets.

    Supports two modes:

    - **Downloaded** (default): the dataset has ``__getitem__`` and a known
      length.  Random access is efficient.
    - **Streaming**: the dataset is an ``IterableDataset`` with sequential
      access only.  Length is unknown until the full dataset has been iterated.

    Parameters
    ----------
    dataset
        A HuggingFace ``Dataset`` or ``IterableDataset``.
    mapping : ColumnMapping
        Describes how to map HF column names to asebytes flat-dict keys.
    cache_size : int
        Maximum number of rows to keep in the LRU cache.  Default 1000.
    """

    def __init__(
        self,
        dataset,
        mapping: ColumnMapping,
        cache_size: int = 1000,
    ):
        self._dataset = dataset
        self._mapping = mapping
        self._cache_size = cache_size
        self._cache: OrderedDict[int, dict[str, Any]] = OrderedDict()

        # Detect streaming vs downloaded
        # IterableDataset may have __getitem__ but never __len__
        self._streaming = not hasattr(dataset, "__len__")

        if self._streaming:
            self._length: int | None = self._probe_length(dataset)
            self._stream_iter: Iterator | None = None
            self._stream_pos: int = 0
        else:
            self._length = len(dataset)

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the streaming iterator to prevent cleanup errors at exit."""
        if self._streaming and self._stream_iter is not None:
            if hasattr(self._stream_iter, "close"):
                self._stream_iter.close()
            self._stream_iter = None

    def __del__(self) -> None:
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ── Metadata helpers ──────────────────────────────────────────────────

    @staticmethod
    def _probe_length(dataset) -> int | None:
        """Try to discover the dataset length from Hub metadata.

        HuggingFace ``IterableDataset`` objects carry an ``.info.splits``
        attribute populated from the Hub API.  If the split info contains
        ``num_examples``, we can know the length without iterating.
        """
        try:
            info = dataset.info
            if info is None or info.splits is None:
                return None
            split_name = getattr(dataset, "split", None)
            if split_name is not None:
                split_name = str(split_name)
            if split_name and split_name in info.splits:
                n = info.splits[split_name].num_examples
                if n is not None and n > 0:
                    return n
        except (AttributeError, KeyError, TypeError):
            pass
        return None

    # ── LRU cache helpers ─────────────────────────────────────────────────

    def _cache_put(self, index: int, row: dict[str, Any]) -> None:
        """Insert or update LRU cache, evicting oldest if at capacity."""
        if index in self._cache:
            self._cache[index] = row
            self._cache.move_to_end(index)
            return
        self._cache[index] = row
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    def _cache_get(self, index: int) -> dict[str, Any] | None:
        """Return cached row or None, updating LRU order on hit."""
        if index in self._cache:
            self._cache.move_to_end(index)
            return self._cache[index]
        return None

    # ── Streaming helpers ─────────────────────────────────────────────────

    def _ensure_stream(self) -> Iterator:
        """Return the current stream iterator, creating one if needed."""
        if self._stream_iter is None:
            self._stream_iter = iter(self._dataset)
            self._stream_pos = 0
        return self._stream_iter

    def _restart_stream(self) -> Iterator:
        """Restart the stream iterator from the beginning."""
        self._stream_iter = iter(self._dataset)
        self._stream_pos = 0
        return self._stream_iter

    def _stream_to(self, index: int) -> dict[str, Any]:
        """Advance the stream to *index*, caching every row along the way.

        If *index* is behind the current stream position, the stream is
        restarted.  For cached intermediate rows, the iterator is still
        advanced (to keep it in sync) but ``apply()`` is not re-called.
        """
        it = self._ensure_stream()

        # Need to go backwards? Restart.
        if index < self._stream_pos:
            it = self._restart_stream()

        # Advance to the target index
        while self._stream_pos <= index:
            # Check cache first (useful after restart)
            cached = self._cache_get(self._stream_pos)
            if cached is not None:
                if self._stream_pos == index:
                    # Target row is already cached — return without consuming iterator
                    self._stream_pos += 1
                    return cached
                # Intermediate cached row — still must advance iterator to stay in sync
                try:
                    next(it)
                except StopIteration:
                    self._length = self._stream_pos
                    raise IndexError(index) from None
                self._stream_pos += 1
                continue

            try:
                hf_row = next(it)
            except StopIteration:
                self._length = self._stream_pos
                raise IndexError(index) from None

            row = self._mapping.apply(hf_row)
            self._cache_put(self._stream_pos, row)
            if self._stream_pos == index:
                self._stream_pos += 1
                return row
            self._stream_pos += 1

        # Should not reach here
        raise IndexError(index)  # pragma: no cover

    # ── ReadableBackend interface ─────────────────────────────────────────

    def __len__(self) -> int:
        if self._length is None:
            raise TypeError(
                "Length unknown for streaming dataset. "
                "Iterate through all rows to discover the length, "
                "or use a downloaded (non-streaming) dataset."
            )
        return self._length

    def columns(self, index: int = 0) -> list[str]:
        row = self.read_row(index)
        return list(row.keys())

    def read_row(
        self, index: int, keys: list[str] | None = None
    ) -> dict[str, Any]:
        # Handle negative indexing for downloaded mode
        if index < 0:
            if self._streaming and self._length is None:
                raise IndexError(
                    "Negative indexing not supported for streaming datasets "
                    "with unknown length."
                )
            if self._length is not None:
                index = index + self._length

        # Bounds check for downloaded mode
        if not self._streaming and (index < 0 or index >= self._length):
            raise IndexError(index)

        # Check cache
        cached = self._cache_get(index)
        if cached is not None:
            if keys is not None:
                return {k: cached[k] for k in keys if k in cached}
            return cached

        if self._streaming:
            row = self._stream_to(index)
        else:
            # Downloaded mode: direct access
            hf_row = self._dataset[index]
            row = self._mapping.apply(hf_row)
            self._cache_put(index, row)

        if keys is not None:
            return {k: row[k] for k in keys if k in row}
        return row

    def read_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> list[dict[str, Any]]:
        return [self.read_row(i, keys) for i in indices]

    def iter_rows(
        self, indices: list[int], keys: list[str] | None = None
    ) -> Iterator[dict[str, Any]]:
        for i in indices:
            yield self.read_row(i, keys)

    def read_column(
        self, key: str, indices: list[int] | None = None
    ) -> list[Any]:
        if indices is None:
            if self._streaming and self._length is None:
                raise TypeError(
                    "Cannot read full column from streaming dataset with "
                    "unknown length. Pass explicit indices or iterate "
                    "through the dataset first."
                )
            indices = list(range(len(self)))
        return [self.read_row(i, [key])[key] for i in indices]

    # ── Class method: from_uri ────────────────────────────────────────────

    @classmethod
    def from_uri(
        cls,
        uri: str,
        *,
        mapping: ColumnMapping | None = None,
        streaming: bool = True,
        split: str | None = None,
        cache_size: int = 1000,
        **load_kwargs,
    ) -> HuggingFaceBackend:
        """Construct a backend from a URI string.

        Supported URI schemes:

        - ``hf://user/dataset`` -- generic HuggingFace dataset (mapping required)
        - ``colabfit://dataset`` -- auto-prepends ``colabfit/`` org if needed,
          uses the :data:`COLABFIT` mapping by default
        - ``optimade://provider/structures`` -- uses the :data:`OPTIMADE`
          mapping by default

        Parameters
        ----------
        uri : str
            URI of the form ``scheme://path``.
        mapping : ColumnMapping or None
            Column mapping. If None, a default mapping is chosen based on
            the scheme (required for ``hf://``).
        streaming : bool
            Whether to load the dataset in streaming mode.
        split : str or None
            Dataset split to load (e.g. ``"train"``).
        cache_size : int
            LRU cache size for the backend.
        **load_kwargs
            Extra keyword arguments forwarded to ``datasets.load_dataset``.
        """
        if "://" not in uri:
            raise ValueError(f"Invalid URI (expected 'scheme://path'): {uri!r}")
        scheme, remainder = uri.split("://", 1)
        if not remainder:
            raise ValueError(f"Empty path in URI: {uri!r}")

        # Scheme-specific defaults
        if scheme == "hf":
            hf_path = remainder
            if mapping is None:
                raise ValueError(
                    "A mapping is required for hf:// URIs. "
                    "Pass mapping=ColumnMapping(...) or use a scheme with "
                    "a default mapping (e.g. colabfit://, optimade://)."
                )
        elif scheme == "colabfit":
            # Auto-prepend org if the remainder has no slash
            if "/" not in remainder:
                hf_path = f"colabfit/{remainder}"
            else:
                hf_path = remainder
            if mapping is None:
                mapping = COLABFIT
        elif scheme == "optimade":
            hf_path = remainder
            if mapping is None:
                mapping = OPTIMADE
        else:
            raise ValueError(f"Unknown URI scheme: {scheme!r}")

        dataset = load_dataset(
            hf_path, streaming=streaming, split=split, **load_kwargs
        )

        # load_dataset returns a DatasetDict when no split is specified.
        # Require the user to pick a split explicitly.
        try:
            from datasets import DatasetDict, IterableDatasetDict
            dict_types = (DatasetDict, IterableDatasetDict)
        except ImportError:
            dict_types = ()
        if dict_types and isinstance(dataset, dict_types):
            splits = list(dataset.keys())
            if not splits:
                raise ValueError(f"Dataset '{hf_path}' has no splits.")
            raise ValueError(
                f"Dataset '{hf_path}' has multiple splits: {splits}. "
                f"Please specify one, e.g. split='{splits[0]}'."
            )

        return cls(dataset, mapping=mapping, cache_size=cache_size)
