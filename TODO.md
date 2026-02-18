- [ ] add `positions = db.get_array("arrays.positions", indices=slice(0, 1000))` to `ASEIO` OR better `db.get_array_io("arrays.positions")` whith `Sequence[np.ndarray]` interface for data reader support.
- [ ] zarr backend
- [ ] h5md backend (sensible? We have LMDB which if faster and more flexible?!) only good for post-processing if at all
- [ ] parquet / LeMaterial backend
- [ ] consider splitting lmdb from a single file into multiple (like fairchem does!)
- [ ] https://www.optimade.org/ 
- [ ] https://colabfit.org/


e.g.
```
io = ASEIO("mydata.lmdb") # auto-detect backend uses asebytes.lmdb.LMDBBackend
io = ASEIO(asebytes.zarr.ZarrBackend(...)) # auto-detect backend
# support all the above
```

Use protocol or ABC for backends.
Split into modules with lazy imports and e.g. `uv add asebytes[zarr]`

- [ ] local cache format
```py
io = ASEIO(ZarrBackend(...), cache_to=LMDBBackend(...)) # on first read, data is cached to LMDB for faster subsequent reads, TTL?
```