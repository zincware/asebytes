import pytest

import asebytes


@pytest.fixture
def io(tmp_path):
    return asebytes.BytesIO(str(tmp_path / "test.db"))


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


def test_counter_mapping(io):
    # Test that we can store and retrieve mapping
    # This is an internal test - users won't call these methods directly
    with io.env.begin(write=True) as txn:
        # Store mappings with integer sort keys
        io._set_mapping(txn, 0, 100)
        io._set_mapping(txn, 1, 101)
        io._set_count(txn, 2)
        io._set_next_sort_key(txn, 102)

    with io.env.begin() as txn:
        assert io._get_mapping(txn, 0) == 100
        assert io._get_mapping(txn, 1) == 101
        assert io._get_count(txn) == 2
        assert io._get_next_sort_key(txn) == 102

        # Test allocation
    with io.env.begin(write=True) as txn:
        new_key = io._allocate_sort_key(txn)
        assert new_key == 102
        assert io._get_next_sort_key(txn) == 103


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


def test_get_nonexistent_key(io, ethanol):
    # Test that get() with non-existent keys returns empty dict for those keys
    io[0] = asebytes.encode(ethanol[0])
    data = io.get(0, keys=[b"cell", b"nonexistent.key"])
    assert b"cell" in data
    assert b"nonexistent.key" not in data
    assert len(data) == 1


def test_get_empty_keys_list(io, ethanol):
    # Test that get() with empty keys list returns empty dict
    io[0] = asebytes.encode(ethanol[0])
    data = io.get(0, keys=[])
    assert data == {}


def test_get_nonexistent_index(io):
    # Test that get() raises KeyError for non-existent index
    with pytest.raises(KeyError, match="Index 0 not found"):
        io.get(0)


def test_get_available_keys(io, ethanol):
    # Test that get_available_keys() returns all keys for an index
    io[0] = asebytes.encode(ethanol[0])
    keys = io.get_available_keys(0)
    assert b"cell" in keys
    assert b"pbc" in keys
    assert b"arrays.positions" in keys
    assert b"arrays.numbers" in keys
    assert b"info.smiles" in keys
    assert b"info.connectivity" in keys


def test_get_available_keys_nonexistent_index(io):
    # Test that get_available_keys() raises KeyError for non-existent index
    with pytest.raises(KeyError, match="Index 0 not found"):
        io.get_available_keys(0)


def test_get_available_keys_empty_data(io):
    # Test with minimal atoms data
    minimal_data = {b"cell": b"test", b"pbc": b"test"}
    io[0] = minimal_data
    keys = io.get_available_keys(0)
    assert keys == [b"cell", b"pbc"]
