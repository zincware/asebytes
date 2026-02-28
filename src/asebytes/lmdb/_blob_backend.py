import struct
from collections.abc import Iterator
from typing import Any

import lmdb

from .._backends import ReadWriteBackend

BLOCK_SIZE = 1024


class LMDBBlobBackend(ReadWriteBackend[bytes, bytes]):
    """LMDB-backed read-write backend for byte dictionaries.

    Uses a blocked index + global schema for efficient reads.
    Sort keys are stored in packed blocks of up to BLOCK_SIZE entries,
    and field names are tracked in a single global schema (union of all fields).

    Parameters
    ----------
    file : str
        Path to LMDB database file.
    prefix : bytes, default=b""
        Key prefix for namespacing entries.
    map_size : int, default=10737418240
        Maximum size of the LMDB database in bytes (default 10GB).
    readonly : bool, default=False
        If True, opens database in read-only mode.
    **lmdb_kwargs
        Additional keyword arguments passed to lmdb.open().
    """

    def __init__(
        self,
        file: str,
        prefix: bytes = b"",
        map_size: int = 10737418240,
        readonly: bool = False,
        **lmdb_kwargs,
    ):
        self.file = file
        self.prefix = prefix
        self.env = lmdb.open(
            file,
            map_size=map_size,
            subdir=False,
            readonly=readonly,
            **lmdb_kwargs,
        )
        # Lazily-loaded cache (invalidated on writes)
        self._blocks: list[list[int]] | None = None
        self._schema_cache: list[bytes] | None = None
        self._block_sizes: list[int] | None = None

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def _invalidate_cache(self) -> None:
        self._blocks = None
        self._schema_cache = None
        self._block_sizes = None

    def _ensure_cache(self, txn) -> None:
        """Load blocks + schema from LMDB if not already cached."""
        if self._blocks is not None:
            return

        # Schema
        schema_bytes = txn.get(self.prefix + b"__schema__")
        if schema_bytes is not None and schema_bytes:
            self._schema_cache = schema_bytes.split(b"\n")
        else:
            self._schema_cache = []

        # Block count
        blk_count_bytes = txn.get(self.prefix + b"__blk_count__")
        if blk_count_bytes is None:
            self._blocks = []
            self._block_sizes = []
            return

        n_blocks = struct.unpack("<I", blk_count_bytes)[0]

        # Block sizes
        sizes_bytes = txn.get(self.prefix + b"__blk_sizes__")
        self._block_sizes = list(struct.unpack(f"<{n_blocks}I", sizes_bytes))

        # Load all blocks
        self._blocks = []
        for i in range(n_blocks):
            blk_key = self.prefix + b"__blk__" + struct.pack("<I", i)
            blk_bytes = txn.get(blk_key)
            size = self._block_sizes[i]
            sort_keys = list(struct.unpack(f"<{size}Q", blk_bytes))
            self._blocks.append(sort_keys)

    # ------------------------------------------------------------------
    # Index resolution (cached, no LMDB lookups)
    # ------------------------------------------------------------------

    def _resolve_sort_key(self, index: int) -> int:
        """Resolve logical index to sort_key using cached blocks."""
        if index < 0:
            raise KeyError(f"Index {index} not found")
        cumsum = 0
        for i, size in enumerate(self._block_sizes):
            if cumsum + size > index:
                return self._blocks[i][index - cumsum]
            cumsum += size
        raise KeyError(f"Index {index} not found")

    def _find_block(self, index: int) -> tuple[int, int]:
        """Find (block_index, local_offset) for a logical index.

        Also handles index == total (append position).
        """
        cumsum = 0
        for i, size in enumerate(self._block_sizes):
            if cumsum + size > index:
                return i, index - cumsum
            cumsum += size
        # index == total count: return end of last block
        if index == cumsum:
            if self._block_sizes:
                last = len(self._block_sizes) - 1
                return last, self._block_sizes[last]
            return 0, 0
        raise IndexError(f"Index {index} out of range")

    # ------------------------------------------------------------------
    # Block persistence helpers
    # ------------------------------------------------------------------

    def _save_block_metadata(self, txn) -> None:
        """Write block count + sizes to LMDB."""
        n_blocks = len(self._blocks)
        txn.put(self.prefix + b"__blk_count__", struct.pack("<I", n_blocks))
        self._block_sizes = [len(blk) for blk in self._blocks]
        if n_blocks:
            txn.put(
                self.prefix + b"__blk_sizes__",
                struct.pack(f"<{n_blocks}I", *self._block_sizes),
            )

    def _save_block(self, txn, block_index: int) -> None:
        """Write a single block to LMDB."""
        blk = self._blocks[block_index]
        blk_key = self.prefix + b"__blk__" + struct.pack("<I", block_index)
        txn.put(blk_key, struct.pack(f"<{len(blk)}Q", *blk))

    def _save_schema(self, txn) -> None:
        """Write global schema to LMDB."""
        txn.put(self.prefix + b"__schema__", b"\n".join(self._schema_cache))

    def _merge_schema(self, field_keys: set[bytes]) -> bool:
        """Merge new field keys into schema. Returns True if schema grew."""
        existing = set(self._schema_cache)
        new_keys = field_keys - existing
        if new_keys:
            self._schema_cache = sorted(existing | new_keys)
            return True
        return False

    # ------------------------------------------------------------------
    # Metadata helpers (count + sort key counter)
    # ------------------------------------------------------------------

    def _get_count(self, txn) -> int:
        """Get the current count from metadata (returns 0 if not set)."""
        count_key = self.prefix + b"__meta__count"
        count_bytes = txn.get(count_key)
        if count_bytes is None:
            return 0
        return int(count_bytes.decode())

    def _set_count(self, txn, count: int) -> None:
        """Set the count in metadata."""
        count_key = self.prefix + b"__meta__count"
        txn.put(count_key, str(count).encode())

    def _get_next_sort_key(self, txn) -> int:
        """Get the next available sort key counter (returns 0 if not set)."""
        key = self.prefix + b"__meta__next_sort_key"
        value = txn.get(key)
        if value is None:
            return 0
        return int(value.decode())

    def _set_next_sort_key(self, txn, value: int) -> None:
        """Set the next available sort key counter."""
        key = self.prefix + b"__meta__next_sort_key"
        txn.put(key, str(value).encode())

    def _allocate_sort_key(self, txn) -> int:
        """Allocate a new unique sort key by incrementing the counter."""
        next_key = self._get_next_sort_key(txn)
        self._set_next_sort_key(txn, next_key + 1)
        return next_key

    # ------------------------------------------------------------------
    # ReadBackend implementation
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        with self.env.begin() as txn:
            return self._get_count(txn)

    def get(
        self, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes]:
        """Get data at index, optionally filtering to specific keys."""
        with self.env.begin() as txn:
            return self.get_with_txn(txn, index, keys)

    def get_with_txn(
        self, txn, index: int, keys: list[bytes] | None = None
    ) -> dict[bytes, bytes]:
        """Get data at index using an existing LMDB transaction."""
        self._ensure_cache(txn)
        sort_key = self._resolve_sort_key(index)
        sort_key_str = str(sort_key).encode()
        prefix = self.prefix + sort_key_str + b"-"

        if keys is not None:
            keys_set = set(keys)
            keys_to_fetch = [prefix + f for f in keys_set]
        else:
            keys_set = None
            keys_to_fetch = [prefix + f for f in self._schema_cache]

        result = {}
        if keys_to_fetch:
            cursor = txn.cursor()
            for key, value in cursor.getmulti(keys_to_fetch):
                field_name = key[len(prefix):]
                result[field_name] = value

        if keys_set is not None and len(result) != len(keys_set):
            retrieved_keys = set(result.keys())
            invalid_keys = keys_set - retrieved_keys
            raise KeyError(
                f"Invalid keys at index {index}: {sorted(invalid_keys)}"
            )

        # If caller didn't request specific keys and got nothing, it's a None placeholder
        if keys_set is None and not result:
            return None
        return result

    def keys(self, index: int) -> list[bytes]:
        """Get all available keys for a given index."""
        with self.env.begin() as txn:
            self._ensure_cache(txn)
            sort_key = self._resolve_sort_key(index)
            sort_key_str = str(sort_key).encode()
            prefix = self.prefix + sort_key_str + b"-"

            keys_to_check = [prefix + f for f in self._schema_cache]
            result = []
            if keys_to_check:
                cursor = txn.cursor()
                for key, _ in cursor.getmulti(keys_to_check):
                    result.append(key[len(prefix):])
            return result

    def get_many(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> list[dict[bytes, bytes] | None]:
        """Optimized bulk read using a single LMDB transaction."""
        with self.env.begin() as txn:
            return [self.get_with_txn(txn, i, keys) for i in indices]

    def iter_rows(
        self, indices: list[int], keys: list[bytes] | None = None
    ) -> Iterator[dict[bytes, bytes] | None]:
        """Yield rows within a single LMDB read transaction."""
        with self.env.begin() as txn:
            for i in indices:
                yield self.get_with_txn(txn, i, keys)

    # ------------------------------------------------------------------
    # ReadWriteBackend implementation
    # ------------------------------------------------------------------

    def set(self, index: int, data: dict[bytes, bytes] | None) -> None:
        """Write or overwrite a single row."""
        if data is None:
            data = {}
        with self.env.begin(write=True) as txn:
            self._ensure_cache(txn)
            current_count = self._get_count(txn)

            if index < current_count:
                # Overwrite existing entry
                sort_key = self._resolve_sort_key(index)

                # Delete old data using schema
                sort_key_str = str(sort_key).encode()
                prefix = self.prefix + sort_key_str + b"-"
                for field in self._schema_cache:
                    txn.delete(prefix + field)
            else:
                # Append new entry
                sort_key = self._allocate_sort_key(txn)

                # Add sort_key to blocks
                if not self._blocks or len(self._blocks[-1]) >= BLOCK_SIZE:
                    self._blocks.append([sort_key])
                else:
                    self._blocks[-1].append(sort_key)

                # Save affected block + metadata
                self._save_block(txn, len(self._blocks) - 1)
                self._save_block_metadata(txn)

            # Write new data
            sort_key_str = str(sort_key).encode()
            items_to_insert = [
                (self.prefix + sort_key_str + b"-" + key, value)
                for key, value in data.items()
            ]
            if items_to_insert:
                cursor = txn.cursor()
                cursor.putmulti(items_to_insert, dupdata=False)

            # Update schema
            if self._merge_schema(set(data.keys())):
                self._save_schema(txn)

            # Update count
            if index >= current_count:
                self._set_count(txn, index + 1)

        self._invalidate_cache()

    def delete(self, index: int) -> None:
        """Delete a row at index, shifting subsequent rows."""
        with self.env.begin(write=True) as txn:
            self._ensure_cache(txn)
            current_count = self._get_count(txn)

            if index < 0:
                index += current_count
            if index < 0 or index >= current_count:
                raise IndexError(
                    f"Index {index} out of range [0, {current_count})"
                )

            # Find block and sort_key
            blk_idx, local = self._find_block(index)
            sort_key = self._blocks[blk_idx][local]

            # Remove from block
            self._blocks[blk_idx].pop(local)

            if not self._blocks[blk_idx]:
                # Block is empty -- remove it and shift subsequent block keys
                n_before = len(self._blocks)
                self._blocks.pop(blk_idx)
                # Rewrite shifted blocks
                for i in range(blk_idx, len(self._blocks)):
                    self._save_block(txn, i)
                # Delete the old last block key
                old_last_key = (
                    self.prefix + b"__blk__" + struct.pack("<I", n_before - 1)
                )
                txn.delete(old_last_key)
            else:
                self._save_block(txn, blk_idx)

            self._save_block_metadata(txn)

            # Delete data keys using schema
            sort_key_str = str(sort_key).encode()
            prefix = self.prefix + sort_key_str + b"-"
            for field in self._schema_cache:
                txn.delete(prefix + field)

            # Update count
            self._set_count(txn, current_count - 1)

        self._invalidate_cache()

    def insert(self, index: int, value: dict[bytes, bytes] | None) -> None:
        """Insert a row at index, shifting subsequent rows."""
        if value is None:
            value = {}
        with self.env.begin(write=True) as txn:
            self._ensure_cache(txn)
            current_count = self._get_count(txn)

            # Clamp index to valid range [0, count]
            if index < 0:
                index = 0
            if index > current_count:
                index = current_count

            sort_key = self._allocate_sort_key(txn)

            if not self._blocks:
                # First entry ever
                self._blocks.append([sort_key])
                self._save_block(txn, 0)
            else:
                blk_idx, local = self._find_block(index)
                self._blocks[blk_idx].insert(local, sort_key)

                # Split if block overflows
                if len(self._blocks[blk_idx]) > BLOCK_SIZE:
                    mid = len(self._blocks[blk_idx]) // 2
                    left = self._blocks[blk_idx][:mid]
                    right = self._blocks[blk_idx][mid:]
                    self._blocks[blk_idx] = left
                    self._blocks.insert(blk_idx + 1, right)
                    # Rewrite split block and all shifted blocks
                    for i in range(blk_idx, len(self._blocks)):
                        self._save_block(txn, i)
                else:
                    self._save_block(txn, blk_idx)

            self._save_block_metadata(txn)

            # Write data
            sort_key_str = str(sort_key).encode()
            items_to_insert = [
                (self.prefix + sort_key_str + b"-" + key, val)
                for key, val in value.items()
            ]
            if items_to_insert:
                cursor = txn.cursor()
                cursor.putmulti(items_to_insert, dupdata=False)

            # Update schema
            if self._merge_schema(set(value.keys())):
                self._save_schema(txn)

            # Update count
            self._set_count(txn, current_count + 1)

        self._invalidate_cache()

    def extend(self, values: list[dict[bytes, bytes] | None]) -> int:
        """Efficiently extend with multiple items using bulk operations."""
        if not values:
            return len(self)

        with self.env.begin(write=True) as txn:
            self._ensure_cache(txn)
            current_count = self._get_count(txn)

            # Allocate all sort keys at once
            next_key = self._get_next_sort_key(txn)
            n = len(values)
            sort_keys = list(range(next_key, next_key + n))
            self._set_next_sort_key(txn, next_key + n)

            all_items = []
            modified_blocks: set[int] = set()
            all_field_keys: set[bytes] = set()

            for sort_key, item in zip(sort_keys, values):
                if item is None:
                    item = {}
                sort_key_str = str(sort_key).encode()

                # Add sort_key to blocks
                if (
                    not self._blocks
                    or len(self._blocks[-1]) >= BLOCK_SIZE
                ):
                    self._blocks.append([sort_key])
                    modified_blocks.add(len(self._blocks) - 1)
                else:
                    self._blocks[-1].append(sort_key)
                    modified_blocks.add(len(self._blocks) - 1)

                # Collect data entries
                for field_key, field_value in item.items():
                    data_key = self.prefix + sort_key_str + b"-" + field_key
                    all_items.append((data_key, field_value))

                all_field_keys.update(item.keys())

            # Save modified blocks into the putmulti batch
            for blk_idx in modified_blocks:
                blk = self._blocks[blk_idx]
                blk_key = (
                    self.prefix + b"__blk__" + struct.pack("<I", blk_idx)
                )
                all_items.append(
                    (blk_key, struct.pack(f"<{len(blk)}Q", *blk))
                )

            # Block metadata
            n_blocks = len(self._blocks)
            self._block_sizes = [len(blk) for blk in self._blocks]
            all_items.append(
                (
                    self.prefix + b"__blk_count__",
                    struct.pack("<I", n_blocks),
                )
            )
            if n_blocks:
                all_items.append(
                    (
                        self.prefix + b"__blk_sizes__",
                        struct.pack(
                            f"<{n_blocks}I", *self._block_sizes
                        ),
                    )
                )

            # Update schema
            if self._merge_schema(all_field_keys):
                all_items.append(
                    (
                        self.prefix + b"__schema__",
                        b"\n".join(self._schema_cache),
                    )
                )

            # Bulk insert everything
            cursor = txn.cursor()
            cursor.putmulti(all_items, dupdata=False, overwrite=True)

            # Update count
            self._set_count(txn, current_count + n)

        self._invalidate_cache()
        return current_count + n

    def update(self, index: int, data: dict[bytes, bytes]) -> None:
        """Optimized partial update -- only writes changed keys."""
        if not data:
            return

        with self.env.begin(write=True) as txn:
            self._ensure_cache(txn)
            sort_key = self._resolve_sort_key(index)
            sort_key_str = str(sort_key).encode()
            prefix = self.prefix + sort_key_str + b"-"

            items_to_update = [
                (prefix + field_key, value)
                for field_key, value in data.items()
            ]

            if items_to_update:
                cursor = txn.cursor()
                cursor.putmulti(items_to_update, dupdata=False, overwrite=True)

            # Update schema if new fields
            if self._merge_schema(set(data.keys())):
                self._save_schema(txn)

        self._invalidate_cache()

    def update_many(self, start: int, data: list[dict[bytes, bytes]]) -> None:
        """Batch partial-merge in a single LMDB transaction."""
        if not data:
            return
        with self.env.begin(write=True) as txn:
            self._ensure_cache(txn)
            all_items = []
            new_fields: set[bytes] = set()
            for i, row_data in enumerate(data):
                if not row_data:
                    continue
                sort_key = self._resolve_sort_key(start + i)
                sort_key_str = str(sort_key).encode()
                prefix = self.prefix + sort_key_str + b"-"
                for field_key, value in row_data.items():
                    all_items.append((prefix + field_key, value))
                new_fields.update(row_data.keys())
            if all_items:
                cursor = txn.cursor()
                cursor.putmulti(all_items, dupdata=False, overwrite=True)
            if self._merge_schema(new_fields):
                self._save_schema(txn)
        self._invalidate_cache()

    def set_column(self, key: bytes, start: int, values: list[bytes]) -> None:
        """Write a single key across contiguous rows in a single LMDB transaction."""
        if not values:
            return
        with self.env.begin(write=True) as txn:
            self._ensure_cache(txn)
            all_items = []
            for i, value in enumerate(values):
                sort_key = self._resolve_sort_key(start + i)
                sort_key_str = str(sort_key).encode()
                all_items.append((self.prefix + sort_key_str + b"-" + key, value))
            if all_items:
                cursor = txn.cursor()
                cursor.putmulti(all_items, dupdata=False, overwrite=True)
            if self._merge_schema({key}):
                self._save_schema(txn)
        self._invalidate_cache()
