# Unified Trajectory Interface for Atomistic Simulation Data

## SOTA
most interfaces can read a multitude of different file formats, (MDAnalysis, chemfiles, ase, ...) but their focus is on local MD trajectories.
Are rare exception is https://github.com/Becksteinlab/zarrtraj support for MDAnalysis to r/w cloud-native zarr files.
An ASE which can connect to SQL storage (including remote postrgresql)

## Challange
Machine-learned interatomic potentials require
- massive amounts of data (millions+) for foundation models
- hetereogeniouse data with different numbers of datoms / different properties / mutli-fidelity, e.g. energies from different QM methods
- searchabilitiy, e.g. I have ethanol, how many other ethanols are there (smiles?) but also structural similiarity and ideally hash lookups on the atomic positions
- high performance with streaming and caching support for data training

## Design
- `MutableSequence[ase.Atoms]` as interface for reading / writing 
- fileformat agnostic, e.g. support for LMDB, H5, Zarr, XYZ

## Standards
- H5MD (znh5md library)
- ZarrTraj
- SQL / nosql

## Questions
- What file formats for cloude native are required, e.g. parquet? Storage on huggingface?
- Highest performance
- data prefetching
- torch / tf dataloader support
- ASE is great, but direct property to numpy support is also important
- REDIS cache support / middleware for maximum performance sensible?

Use context7 on all relevant libraries and standards.
Use context7 to find existing tooling from the ML / data science and atomistic community that can partially solve this.


```mermaid
flowchart LR
    %% Define Styles (Colors)
    classDef ui fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#000
    classDef protocol fill:#f3e8ff,stroke:#9333ea,stroke-width:2px,color:#000
    classDef adapter fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#000
    classDef utility fill:#ffedd5,stroke:#ea580c,stroke-width:2px,color:#000

    BlobReadBackend --> BlobIO
    AsyncBlobReadBackend --> AsyncBlobIO

    BlobReadWriteBackend --> BlobIO
    AsyncBlobReadWriteBackend --> AsyncBlobIO

    ObjectReadBackend --> ObjectIO
    AsyncObjectReadBackend --> AsyncObjectIO

    ObjectReadWriteBackend --> ObjectIO
    AsyncObjectReadWriteBackend --> AsyncObjectIO

    %% If there is no AsyncBackend we use a wrapper
    BlobIO --> SyncToAsyncAdapter --> AsyncBlobIO
    ObjectIO --> SyncToAsyncAdapter --> AsyncObjectIO

    %% convienience ASE Interface
    ObjectIO --> ASEIO
    AsyncObjectIO --> AsyncASEIO

    %% Existing Backends
    LMDBReadWrite --> BlobReadWriteBackend
    HFRead --> ObjectReadBackend
    ZarrReadWrite --> ObjectReadWriteBackend
    H5MDReadWrite --> ObjectReadWriteBackend
    %% special case, because ASE XYZ does result in ASE atoms directly
    XYZRead --> ASEIO

    %% New Backends
    RedisReadWrite --> BlobReadWriteBackend
    AsyncRedisReadWrite --> AsyncBlobReadWriteBackend
    MongoDBReadWrite --> ObjectReadWriteBackend
    AsyncMongoDBReadWrite --> AsyncObjectReadWriteBackend

%% Apply Styles to Nodes
    class BlobIO,AsyncBlobIO,AsyncObjectIO,ObjectIO,ASEIO,AsyncASEIO ui
    class BlobReadBackend,AsyncBlobReadBackend,BlobReadWriteBackend,AsyncBlobReadWriteBackend,ObjectReadBackend,AsyncObjectReadBackend,ObjectReadWriteBackend,AsyncObjectReadWriteBackend protocol
    class LMDBReadWrite,HFRead,ZarrReadWrite,H5MDReadWrite,RedisReadWrite,AsyncRedisReadWrite,MongoDBReadWrite,AsyncMongoDBReadWrite,XYZRead adapter
    class SyncToAsyncAdapter utility
```