# asebytes

Efficient serialization and storage for ASE Atoms objects using LMDB.

## API

- **`to_bytes(atoms)`** - Serialize an ASE Atoms object to a dict of bytes
- **`from_bytes(data)`** - Deserialize bytes back into an ASE Atoms object
- **`BytesIO(file, prefix)`** - LMDB-backed list-like storage for bytes dictionaries
- **`ASEIO(file, prefix)`** - LMDB-backed list-like storage for ASE Atoms objects

## Examples

```python
from asebytes import ASEIO, BytesIO, to_bytes, from_bytes
import molify

# Generate conformers from SMILES
ethanol = molify.smiles2conformers("CCO", numConfs=100)

# Serialize/deserialize single molecule
data = to_bytes(ethanol[0])
atoms_restored = from_bytes(data)

# High-level: Store Atoms objects directly
db = ASEIO("conformers.lmdb")
db.extend(ethanol)  # Add all conformers
mol = db[0]         # Returns ase.Atoms

# Low-level: BytesIO stores serialized data
bytes_db = BytesIO("conformers.lmdb")
bytes_db.append(to_bytes(ethanol[0]))      # Manual serialization
data = bytes_db[0]                         # Returns dict[bytes, bytes]
mol = from_bytes(data)                     # Manual deserialization

# ASEIO = BytesIO + automatic to_bytes/from_bytes
```
