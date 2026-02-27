"""Async API design for asebytes.

Design decisions:
- Separate classes: AsyncASEIO (async) / ASEIO (sync), AsyncBytesIO / BytesIO
- __getitem__ is always sync, returns awaitable views
- Views implement __await__ for smart materialization:
    - single row view  → Atoms (or dict[bytes, bytes] for BytesIO)
    - multi row view   → list[Atoms] (or list[dict[bytes, bytes]])
    - column view      → list[values]
- Views implement __aiter__ for async iteration
- Async method = sync method + "a" prefix (extend → extend, etc.)
- drop() for column/key removal (pandas-style)
- None placeholders for reserving slots without data
- If backend is sync-only, auto-wrap via asyncio.to_thread
- Index-shifting ops (delete, insert) require contiguous slices or single int.
  Arbitrary index lists (e.g. [2, 5, 8]) are only allowed for non-shifting ops
  (set, update, adrop, get). This avoids ambiguous shift semantics in
  concurrent environments. Use set(None) to empty slots without shifting.
"""

import asebytes

# ============================================================
# AsyncASEIO — high-level Atoms interface
# ============================================================

db = asebytes.AsyncASEIO("mongodb://localhost:27017/asebytes_test", group="room-a")

# --- Single item access (awaitable views) ---

atoms = await db[0]                     # sync: atoms = db[0]
atoms = await db[-1]                    # sync: atoms = db[-1]

# --- Bulk read via views ---

atoms_list = await db[0:10]             # sync: db[0:10].to_list()
atoms_list = await db[[0, 5, 42]]       # sync: db[[0, 5, 42]].to_list()

# --- Length ---

n = await db.len()                     # sync: len(db)

# --- Write operations ---

await db.extend([atoms, atoms])        # sync: db.extend([atoms, atoms])
await db[0].set(atoms)                 # sync: db[0] = atoms
await db[0:10].set([atoms] * 10)       # sync: db[0:10] = [atoms] * 10
await db.insert(0, atoms)              # sync: db.insert(0, atoms)
await db[0].delete()                   # sync: del db[0]
await db[0:10].delete()                # sync: del db[0:10]
# await db[[2, 5, 8]].delete()         # TypeError — non-contiguous delete is ambiguous
await db[[2, 5, 8]].set([None] * 3)   # OK — empties slots without shifting

# --- Partial update ---

await db[0].update({"calc.energy": -10.5})             # sync: db.update(0, {"calc.energy": -10.5})

# --- Drop keys (column removal) ---

await db.adrop(keys=["calc.energy"])                     # sync: db.drop(keys=["calc.energy"])
await db[5:10].adrop(keys=["calc.energy"])               # sync: db[5:10].drop(keys=["calc.energy"])
await db.adrop(keys=["calc.energy", "calc.forces"])      # sync: db.drop(keys=["calc.energy", "calc.forces"])

# --- Column access ---

energies = await db["calc.energy"]                       # sync: db["calc.energy"].to_list()
energies = await db["calc.energy"][0:10]                  # sync: db["calc.energy"][0:10].to_list()
cols = await db[["calc.energy", "calc.forces"]]           # sync: db[["calc.energy", "calc.forces"]].to_list()
cols_dict = await db["calc.energy"].to_dict()             # sync: db["calc.energy"].to_dict()

# --- None / placeholder entries ---

await db.extend([None, None, None])                     # sync: db.extend([None, None, None])
await db.insert(0, None)                                # sync: db.insert(0, None)
await db[0].set(None)                                   # sync: db[0] = None
await db[0:3].set([None, None, None])                   # sync: db[0:3] = [None, None, None]
result = await db[0]                                     # sync: db[0]  → None
results = await db[0:3]                                  # sync: db[0:3].to_list() → [None, None, None]

# --- Async iteration ---

async for atoms in db:                                   # sync: for atoms in db:
    print(atoms)

async for atoms in db[10:100]:                           # sync: for atoms in db[10:100]:
    print(atoms)

async for row in db[["calc.energy", "calc.forces"]]:     # sync: for row in db[["calc.energy", "calc.forces"]]:
    print(row)

async for row in db["calc.energy"][10:100]:              # sync: for val in db["calc.energy"][10:100]:
    print(row)

# --- Chunked async iteration ---

async for atoms in db[0:10000].achunked(1000):           # sync: for atoms in db[0:10000].chunked(1000):
    print(atoms)

# --- Context manager (connection lifecycle) ---

async with asebytes.AsyncASEIO("mongodb://...") as db:   # sync: with asebytes.ASEIO("data.lmdb") as db:
    atoms = await db[0]                                  #           atoms = db[0]


# ============================================================
# AsyncBytesIO — low-level dict[bytes, bytes] interface
# ============================================================

data: dict[bytes, bytes] = {b"calc.energy": b"\x00", b"arrays.positions": b"\x01\x02"}

io = asebytes.AsyncBytesIO("mongodb://localhost:27017/asebytes_test", group="room-a")

# --- Single item access ---

row = await io[0]                                        # sync: io[0]  → dict[bytes, bytes]
row = await io[-1]                                       # sync: io[-1]

# --- Bulk read ---

rows = await io[0:10]                                    # sync: io[0:10].to_list()
rows = await io[[0, 5, 42]]                              # sync: io[[0, 5, 42]].to_list()

# --- Length ---

n = await io.len()                                      # sync: len(io)

# --- Write operations ---

await io.extend([data, data])                           # sync: io.extend([data, data])
await io[0].set(data)                                   # sync: io[0] = data
await io[0:10].set([data] * 10)                         # sync: io[0:10] = [data] * 10
await io.insert(0, data)                                # sync: io.insert(0, data)
await io[0].delete()                                    # sync: del io[0]
await io[0:10].delete()                                 # sync: del io[0:10]
# await io[[2, 5, 8]].delete()                           # TypeError — non-contiguous delete
await io[[2, 5, 8]].set([None] * 3)                    # OK — empties slots without shifting

# --- Partial update ---

await io[0].update({b"calc.energy": b"\x99"})           # sync: io.update(0, {b"calc.energy": b"\x99"})

# --- Drop keys ---

await io.adrop(keys=[b"calc.energy"])                    # sync: io.drop(keys=[b"calc.energy"])
await io[5:10].adrop(keys=[b"calc.energy"])              # sync: io[5:10].drop(keys=[b"calc.energy"])

# --- Column filter (key selection) ---
# __getitem__ with list[bytes] returns a column-filtered view (sync, no I/O)

row = await io[[b"calc.energy", b"calc.forces"]][0]      # sync: io[[b"calc.energy", b"calc.forces"]][0]
rows = await io[[b"calc.energy", b"calc.forces"]][0:10]  # sync: io[[b"calc.energy", b"calc.forces"]][0:10].to_list()

# --- Column-filtered update ---

await io[[b"calc.energy"]][0].set(                      # sync: io.update(0, {b"calc.energy": ...})
    {b"calc.energy": b"\x99"}
)
await io[[b"calc.energy"]][0:10].set(                   # sync: io[[b"calc.energy"]][0:10] = ...
    [{b"calc.energy": b"\x99"}] * 10
)

# --- None / placeholder entries ---

await io.extend([None, None, None])                     # sync: io.extend([None, None, None])
await io.insert(0, None)                                # sync: io.insert(0, None)
await io[0].set(None)                                   # sync: io[0] = None
result = await io[0]                                     # sync: io[0]  → None

# --- Async iteration ---

async for row in io:                                     # sync: for row in io:
    print(row)                                           #           dict[bytes, bytes] | None

async for row in io[[b"calc.energy"]][10:100]:           # sync: for row in io[[b"calc.energy"]][10:100]: 
    print(row)

# --- Schema inspection (sync, no I/O for cached schema) ---

schema = io.get_schema()                                 # sync: io.get_schema()
keys = await io[0].akeys()                               # sync: io.get_available_keys(0)

# --- Context manager ---

async with asebytes.AsyncBytesIO("mongodb://...") as io: # sync: N/A (BytesIO auto-opens)
    row = await io[0]

# --- Clear all data (sync) ---
await io.clear()          # sync: db.clear()

# --- remove the entire collection (group=...) ---
await io.remove()         # sync: db.remove()

# --- more efficient extend with empty rows (sync) ---
# no need to check if every entry is None
await io.reserve(1000)    # sync: io.reserve(1000) # faster than io.extend([None] * 1000)


# ============================================================
# Wrapping a sync backend for async use
# ============================================================

# Sync backend auto-wrapped via asyncio.to_thread
db = asebytes.AsyncASEIO("data.lmdb")                   # LMDB is sync, gets SyncToAsyncAdapter
atoms = await db[0]                                      # runs in thread pool

# Natively async backend — no thread pool overhead
db = asebytes.AsyncASEIO("mongodb://localhost:27017/db")  # MongoDB backend is natively async
atoms = await db[0]                                      # direct async I/O


# ============================================================
# Backend Protocols / ABCs
# ============================================================
#
# Two levels:
#   Bytes-level  (dict[bytes, bytes] | None)  — used by BytesIO / AsyncBytesIO
#   Str-level    (dict[str, Any] | None)      — used by ASEIO / AsyncASEIO
#
# Each level has: Readable (sync), Writable (sync), AsyncReadable, AsyncWritable
# A serialization adapter bridges bytes→str (msgpack, etc.)
#
# Sync backends can be auto-wrapped for async via SyncToAsyncAdapter (to_thread).
# Natively async backends (MongoDB/motor) implement the async protocols directly.

# --- Bytes-level protocols (NEW — BytesIO currently has no ABC) ---
# Key type: bytes, Value type: bytes, Row type: dict[bytes, bytes] | None

class RawReadableBackend(ABC):
    """Read-only backend at the raw bytes level."""

    # -- abstract (must implement) --
    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def get_schema(self) -> list[bytes]:
        """Union of all field names across all rows."""
        ...

    @abstractmethod
    def read_row(self, index: int, keys: list[bytes] | None = None) -> dict[bytes, bytes] | None:
        """Read one row. keys=None → all fields. Returns None for placeholders."""
        ...

    # -- optional overrides (have default impls) --
    def get_available_keys(self, index: int) -> list[bytes]:
        """Keys present at this specific index."""
        row = self.read_row(index)
        return list(row.keys()) if row is not None else []

    def read_rows(self, indices: list[int], keys: list[bytes] | None = None) -> list[dict[bytes, bytes] | None]:
        return [self.read_row(i, keys) for i in indices]

    def iter_rows(self, indices: list[int], keys: list[bytes] | None = None) -> Iterator[dict[bytes, bytes] | None]:
        for i in indices:
            yield self.read_row(i, keys)


class RawWritableBackend(RawReadableBackend):
    """Read-write backend at the raw bytes level."""

    # -- abstract (must implement) --
    @abstractmethod
    def write_row(self, index: int, data: dict[bytes, bytes] | None) -> None: ...

    @abstractmethod
    def insert_row(self, index: int, data: dict[bytes, bytes] | None) -> None: ...

    @abstractmethod
    def delete_row(self, index: int) -> None: ...

    @abstractmethod
    def append_rows(self, data: list[dict[bytes, bytes] | None]) -> None: ...

    # -- optional overrides --
    def update_row(self, index: int, data: dict[bytes, bytes]) -> None:
        """Partial update. Default: read-modify-write."""
        row = self.read_row(index) or {}
        row.update(data)
        self.write_row(index, row)

    def delete_rows(self, start: int, stop: int) -> None:
        """Delete contiguous range [start, stop). Default: loop in reverse."""
        for i in range(stop - 1, start - 1, -1):
            self.delete_row(i)

    def write_rows(self, start: int, data: list[dict[bytes, bytes] | None]) -> None:
        """Overwrite contiguous range starting at start. Default: loop."""
        for i, d in enumerate(data):
            self.write_row(start + i, d)

    def drop_keys(self, keys: list[bytes], indices: list[int] | None = None) -> None:
        """Remove specific keys from rows. Default: read-modify-write per row."""
        if indices is None:
            indices = list(range(len(self)))
        key_set = set(keys)
        for i in indices:
            row = self.read_row(i)
            if row is None:
                continue
            pruned = {k: v for k, v in row.items() if k not in key_set}
            self.write_row(i, pruned)

    def reserve(self, count: int) -> None:
        """Append count placeholder (None) entries. Default: append_rows."""
        self.append_rows([None] * count)

    def clear(self) -> None:
        """Remove all data but keep the container. Default: delete all rows."""
        for i in range(len(self) - 1, -1, -1):
            self.delete_row(i)

    def remove(self) -> None:
        """Remove the entire container (collection/file/group). No default — backend-specific."""
        raise NotImplementedError


# --- Str-level protocols (EXISTING, extended with new ops) ---
# These are what ASEIO uses. Currently: ReadableBackend, WritableBackend.
# New methods added to WritableBackend:

class ReadableBackend(ABC):           # EXISTS TODAY — unchanged
    @abstractmethod
    def __len__(self) -> int: ...
    @abstractmethod
    def columns(self, index: int = 0) -> list[str]: ...
    @abstractmethod
    def read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any] | None: ...
    def read_rows(self, indices, keys=None): ...   # has default
    def iter_rows(self, indices, keys=None): ...   # has default
    def read_column(self, key, indices=None): ...   # has default

class WritableBackend(ReadableBackend):  # EXISTS TODAY — extended
    @abstractmethod
    def write_row(self, index: int, data: dict[str, Any] | None) -> None: ...
    @abstractmethod
    def insert_row(self, index: int, data: dict[str, Any] | None) -> None: ...
    @abstractmethod
    def delete_row(self, index: int) -> None: ...
    @abstractmethod
    def append_rows(self, data: list[dict[str, Any] | None]) -> None: ...
    def update_row(self, index, data): ...          # has default

    # NEW — all have default impls, backends can optimize
    def delete_rows(self, start: int, stop: int) -> None: ...
    def write_rows(self, start: int, data: list[dict[str, Any] | None]) -> None: ...
    def drop_keys(self, keys: list[str], indices: list[int] | None = None) -> None: ...
    def reserve(self, count: int) -> None: ...
    def clear(self) -> None: ...
    def remove(self) -> None: ...


# --- Async protocols (NEW — mirror sync with async methods) ---
# Same method names, all async. Used by AsyncASEIO / AsyncBytesIO.

class AsyncRawReadableBackend(ABC):
    """Async read-only backend at the raw bytes level."""
    @abstractmethod
    async def len(self) -> int: ...
    @abstractmethod
    async def get_schema(self) -> list[bytes]: ...
    @abstractmethod
    async def read_row(self, index: int, keys: list[bytes] | None = None) -> dict[bytes, bytes] | None: ...
    async def get_available_keys(self, index: int) -> list[bytes]: ...  # default
    async def read_rows(self, indices, keys=None): ...                   # default
    async def iter_rows(self, indices, keys=None) -> AsyncIterator: ...  # default


class AsyncRawWritableBackend(AsyncRawReadableBackend):
    """Async read-write backend at the raw bytes level."""
    @abstractmethod
    async def write_row(self, index: int, data: dict[bytes, bytes] | None) -> None: ...
    @abstractmethod
    async def insert_row(self, index: int, data: dict[bytes, bytes] | None) -> None: ...
    @abstractmethod
    async def delete_row(self, index: int) -> None: ...
    @abstractmethod
    async def append_rows(self, data: list[dict[bytes, bytes] | None]) -> None: ...
    async def update_row(self, index, data): ...       # default: read-modify-write
    async def delete_rows(self, start, stop): ...      # default: loop
    async def write_rows(self, start, data): ...       # default: loop
    async def drop_keys(self, keys, indices=None): ... # default: read-modify-write
    async def reserve(self, count): ...                # default: append_rows([None]*count)
    async def clear(self): ...                         # default: delete all
    async def remove(self): ...                        # no default


class AsyncReadableBackend(ABC):
    """Async read-only backend at the str/Any level."""
    @abstractmethod
    async def len(self) -> int: ...
    @abstractmethod
    async def columns(self, index: int = 0) -> list[str]: ...
    @abstractmethod
    async def read_row(self, index: int, keys: list[str] | None = None) -> dict[str, Any] | None: ...
    async def read_rows(self, indices, keys=None): ...
    async def iter_rows(self, indices, keys=None) -> AsyncIterator: ...
    async def read_column(self, key, indices=None): ...


class AsyncWritableBackend(AsyncReadableBackend):
    """Async read-write backend at the str/Any level."""
    @abstractmethod
    async def write_row(self, index: int, data: dict[str, Any] | None) -> None: ...
    @abstractmethod
    async def insert_row(self, index: int, data: dict[str, Any] | None) -> None: ...
    @abstractmethod
    async def delete_row(self, index: int) -> None: ...
    @abstractmethod
    async def append_rows(self, data: list[dict[str, Any] | None]) -> None: ...
    async def update_row(self, index, data): ...
    async def delete_rows(self, start, stop): ...
    async def write_rows(self, start, data): ...
    async def drop_keys(self, keys, indices=None): ...
    async def reserve(self, count): ...
    async def clear(self): ...
    async def remove(self): ...


# --- SyncToAsyncAdapter (auto-wraps any sync backend for async use) ---
# Used when e.g. AsyncASEIO("data.lmdb") wraps the sync LMDBBackend.

class SyncToAsyncRawAdapter(AsyncRawWritableBackend):
    """Wraps a sync RawWritableBackend, runs all methods via asyncio.to_thread."""
    def __init__(self, sync_backend: RawWritableBackend): ...
    async def read_row(self, index, keys=None):
        return await asyncio.to_thread(self._sync.read_row, index, keys)
    # ... same pattern for all methods ...


class SyncToAsyncAdapter(AsyncWritableBackend):
    """Wraps a sync WritableBackend, runs all methods via asyncio.to_thread."""
    def __init__(self, sync_backend: WritableBackend): ...
    async def read_row(self, index, keys=None):
        return await asyncio.to_thread(self._sync.read_row, index, keys)
    # ... same pattern for all methods ...


# --- Serialization adapter (bridges bytes→str level) ---
# This is what LMDBBackend does today: wraps BytesIO + msgpack.
# Generalized so any RawBackend can be lifted to str-level.

class SerializingBackend(WritableBackend):
    """Wraps a RawWritableBackend with ser/de (e.g. msgpack).

    Converts dict[str, Any] ↔ dict[bytes, bytes] using a pluggable serializer.
    This replaces the current LMDBBackend pattern of hardcoding msgpack.
    """
    def __init__(self, raw: RawWritableBackend, serializer=MsgpackSerializer()): ...

class AsyncSerializingBackend(AsyncWritableBackend):
    """Async version: wraps AsyncRawWritableBackend with ser/de."""
    def __init__(self, raw: AsyncRawWritableBackend, serializer=MsgpackSerializer()): ...


# --- Example backend implementations ---

# LMDB (sync native → auto-wrapped for async)
lmdb_raw = LMDBRawBackend("data.lmdb", prefix=b"atoms/")       # implements RawWritableBackend
lmdb_str = SerializingBackend(lmdb_raw)                          # implements WritableBackend
sync_db  = asebytes.ASEIO(lmdb_str)                             # sync ASEIO
async_db = asebytes.AsyncASEIO("data.lmdb")                     # auto: LMDB → SyncToAsync

# MongoDB (async native)
mongo_raw = MongoRawBackend("mongodb://...", group="room-a")     # implements AsyncRawWritableBackend
mongo_str = AsyncSerializingBackend(mongo_raw)                    # implements AsyncWritableBackend
async_db  = asebytes.AsyncASEIO(mongo_str)                       # async ASEIO

# BytesIO level (skip serialization, raw bytes)
sync_io  = asebytes.BytesIO(lmdb_raw)                           # sync BytesIO over LMDB
async_io = asebytes.AsyncBytesIO(mongo_raw)                      # async BytesIO over MongoDB
async_io = asebytes.AsyncBytesIO("data.lmdb")                   # auto: LMDB → SyncToAsync
