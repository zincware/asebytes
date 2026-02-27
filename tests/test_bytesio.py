import pytest

import asebytes


@pytest.fixture
def io(tmp_path):
    return asebytes.BlobIO(asebytes.LMDBBlobBackend(str(tmp_path / "test.lmdb")))


def test_set_get(io, ethanol):
    io[0] = asebytes.encode(ethanol[0])
    data = io[0]
    atoms = asebytes.decode(data)
    assert atoms == ethanol[0]


def test_set_overwrite(io, ethanol):
    atoms = ethanol[0]
    atoms.info["test"] = 1
    io[0] = asebytes.encode(atoms)
    # overwrite with different info
    io[0] = asebytes.encode(ethanol[1])
    atoms = asebytes.decode(io[0])
    assert "test" not in atoms.info


def test_len(io, ethanol):
    for i, atom in enumerate(ethanol):
        io[i] = asebytes.encode(atom)
    assert len(io) == len(ethanol)


def test_append(io, ethanol):
    for atom in ethanol:
        io[len(io)] = asebytes.encode(atom)
    assert len(io) == len(ethanol)


def test_extend(io, ethanol):
    batch = [asebytes.encode(atom) for atom in ethanol]
    io.extend(batch)
    assert len(io) == len(ethanol)


def test_delete(io, ethanol):
    for i, atom in enumerate(ethanol):
        io[i] = asebytes.encode(atom)
    del io[1]
    assert len(io) == len(ethanol) - 1
    atoms = [asebytes.decode(io[i]) for i in range(len(io))]
    expected = [ethanol[0]] + ethanol[2:]
    assert atoms == expected


def test_insert(io, ethanol):
    for i, atom in enumerate(ethanol):
        io[i] = asebytes.encode(atom)
    new_atom = asebytes.encode(ethanol[0])
    io.insert(1, new_atom)
    assert len(io) == len(ethanol) + 1
    atoms = [asebytes.decode(io[i]) for i in range(len(io))]
    expected = [ethanol[0], ethanol[0]] + ethanol[1:]
    assert atoms == expected


def test_iter(io, ethanol):
    for i, atom in enumerate(ethanol):
        io[i] = asebytes.encode(atom)
    atoms = [asebytes.decode(data) for data in io]
    assert atoms == list(ethanol)


def test_blocked_index_internals(io):
    # Test that blocked index and sort key allocation work correctly
    with io._backend.env.begin(write=True) as txn:
        io._backend._set_count(txn, 0)
        io._backend._set_next_sort_key(txn, 100)

    with io._backend.env.begin() as txn:
        assert io._backend._get_count(txn) == 0
        assert io._backend._get_next_sort_key(txn) == 100

    # Test sort key allocation
    with io._backend.env.begin(write=True) as txn:
        sk = io._backend._allocate_sort_key(txn)
        assert sk == 100
        assert io._backend._get_next_sort_key(txn) == 101

    # Test that extend populates blocks and schema
    io.extend([{b"field_a": b"v1", b"field_b": b"v2"}])
    with io._backend.env.begin() as txn:
        io._backend._ensure_cache(txn)
        assert len(io._backend._blocks) == 1
        assert len(io._backend._blocks[0]) == 1
        assert io.keys(0) == [b"field_a", b"field_b"]


def test_get_all_keys(io, ethanol):
    # Test that get() without keys parameter returns all data (same as __getitem__)
    io[0] = asebytes.encode(ethanol[0])
    data_from_getitem = io[0]
    data_from_get = io.get(0)
    assert data_from_get == data_from_getitem
    assert b"cell" in data_from_get
    assert b"pbc" in data_from_get
    assert b"arrays.positions" in data_from_get


def test_get_specific_keys(io, ethanol):
    # Test that get() with keys parameter returns only requested keys
    io[0] = asebytes.encode(ethanol[0])
    data = io.get(0, keys=[b"cell", b"arrays.positions"])
    assert data.keys() == {b"cell", b"arrays.positions"}
    assert b"pbc" not in data
    assert b"arrays.numbers" not in data


def test_get_single_key(io, ethanol):
    # Test that get() with a single key works
    io[0] = asebytes.encode(ethanol[0])
    data = io.get(0, keys=[b"cell"])
    assert data.keys() == {b"cell"}
    assert b"pbc" not in data


def test_get_empty_keys_list(io, ethanol):
    # Test that get() with empty keys list returns empty dict
    io[0] = asebytes.encode(ethanol[0])
    data = io.get(0, keys=[])
    assert data == {}


def test_get_nonexistent_index(io):
    # Test that get() raises KeyError for non-existent index
    with pytest.raises(KeyError, match="Index 0 not found"):
        io.get(0)


def test_keys(io, ethanol):
    # Test that keys() returns all keys for an index
    io[0] = asebytes.encode(ethanol[0])
    keys = io.keys(0)
    assert b"cell" in keys
    assert b"pbc" in keys
    assert b"arrays.positions" in keys
    assert b"arrays.numbers" in keys
    assert b"info.smiles" in keys
    assert b"info.connectivity" in keys


def test_keys_nonexistent_index(io):
    # Test that keys() raises KeyError for non-existent index
    with pytest.raises(KeyError, match="Index 0 not found"):
        io.keys(0)


def test_keys_empty_data(io):
    # Test with minimal atoms data
    minimal_data = {b"cell": b"test", b"pbc": b"test"}
    io[0] = minimal_data
    keys = io.keys(0)
    assert keys == [b"cell", b"pbc"]
