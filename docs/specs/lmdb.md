# LMDB Backend

**Layer:** Blob (`ReadWriteBackend[bytes, bytes]`)
**Object access:** `BlobToObjectReadWriteAdapter` (msgpack + msgpack_numpy)
**Async:** `SyncToAsyncAdapter` only (no native async)
**Files:** `src/asebytes/lmdb/_blob_backend.py`, `_backend.py`

## Storage Layout

```mermaid
graph TD
    subgraph "LMDB Directory: {path}/{group}/data.mdb"
        META["__meta__count → int<br>__meta__next_sort_key → int"]
        SCHEMA["__schema__ → 'col1\ncol2\ncol3'"]
        subgraph "Block Index (1024 entries/block)"
            BLK0["__blk__0 → packed uint64[]"]
            BLK1["__blk__1 → packed uint64[]"]
            BLKN["__blk__N → ..."]
            BLKC["__blk_count__ → int"]
            BLKS["__blk_sizes__ → packed uint32[]"]
        end
        subgraph "Row Data (one KV per field)"
            R0["42-arrays.positions → bytes"]
            R1["42-arrays.numbers → bytes"]
            R2["42-calc.energy → bytes"]
            R3["43-arrays.positions → bytes"]
        end
    end

    BLK0 -->|"sort_keys[0..1023]"| R0
```

**Key format:** `{sort_key}-{field_name}` — each field stored as a separate LMDB key-value pair.

**Block index:** Decouples positional indices from sort keys. Blocks hold up to 1024 packed uint64 sort keys. Enables O(1) positional lookup without scanning.

**Schema union:** `__schema__` stores the union of all field names ever written (newline-separated). Used by `get_column()` to know which fields exist.

## Read/Write Flow

```mermaid
sequenceDiagram
    participant F as Facade
    participant A as BlobToObjectAdapter
    participant B as LMDBBlobBackend
    participant DB as LMDB (mmap)

    Note over F,DB: Single Read: db[i]
    F->>A: get(i)
    A->>B: get(i, byte_keys)
    B->>DB: block lookup → sort_key
    B->>DB: cursor.getmulti([sk-field1, sk-field2, ...])
    DB-->>B: raw bytes
    B-->>A: dict[bytes, bytes]
    A-->>F: msgpack.unpackb → dict[str, Any]

    Note over F,DB: Bulk Read: db[:].to_list()
    F->>A: get_many(indices)
    A->>B: get_many(indices, byte_keys)
    B->>DB: single txn: block lookups → sort_keys
    B->>DB: cursor.getmulti(all_keys) in one call
    DB-->>B: all raw bytes
    B-->>A: list[dict[bytes, bytes]]
    A-->>F: [msgpack.unpackb(row) for row in rows]
```

## Performance

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| `len()` | O(1) | Cached `__meta__count`, invalidated on write |
| `get(i)` | O(1) | Block lookup + `cursor.getmulti` |
| `get_many(N)` | O(N) | Single LMDB transaction, one `cursor.getmulti` |
| `get_column(key, N)` | O(N) | Single txn, `cursor.getmulti` for one field across N rows |
| `extend(N)` | O(N) | `cursor.putmulti`, block append |
| `set(i)` | O(F) | F = number of fields, delete old + write new |
| `delete(i)` | O(B) | B = block size, may rewrite block |
| `insert(i)` | O(B) | Block split if needed |

**Benchmark (1000 ethanol, local):**

| Operation | Time |
|-----------|------|
| Trajectory read | 24ms |
| Single read ×1000 | 23ms |
| Column energy | 0.6ms |
| Write trajectory | 14ms |

## Sync/Async Consistency

No native async backend. Async access via `SyncToAsyncAdapter` wrapping `LMDBBlobBackend` with `asyncio.to_thread()`.

## Potential Optimizations

Already optimal for the use case. mmap provides zero-copy reads. `cursor.getmulti` batches all field reads into one syscall. Block index keeps positional lookups O(1).

No changes recommended.
