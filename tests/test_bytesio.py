import pytest

import asebytes


@pytest.fixture
def io(tmp_path):
    return asebytes.BytesIO(str(tmp_path / "test.db"))


def test_set_get(io, ethanol):
    io[0] = asebytes.to_bytes(ethanol[0])
    data = io[0]
    atoms = asebytes.from_bytes(data)
    assert atoms == ethanol[0]


def test_set_overwrite(io, ethanol):
    atoms = ethanol[0]
    atoms.info["test"] = 1
    io[0] = asebytes.to_bytes(atoms)
    # overwrite with different info
    io[0] = asebytes.to_bytes(ethanol[1])
    atoms = asebytes.from_bytes(io[0])
    assert "test" not in atoms.info


def test_len(io, ethanol):
    for i, atom in enumerate(ethanol):
        io[i] = asebytes.to_bytes(atom)
    assert len(io) == len(ethanol)


def test_append(io, ethanol):
    for atom in ethanol:
        io[len(io)] = asebytes.to_bytes(atom)
    assert len(io) == len(ethanol)


def test_extend(io, ethanol):
    batch = [asebytes.to_bytes(atom) for atom in ethanol]
    io.extend(batch)
    assert len(io) == len(ethanol)


def test_delete(io, ethanol):
    for i, atom in enumerate(ethanol):
        io[i] = asebytes.to_bytes(atom)
    del io[1]
    assert len(io) == len(ethanol) - 1
    atoms = [asebytes.from_bytes(io[i]) for i in range(len(io))]
    expected = [ethanol[0]] + ethanol[2:]
    assert atoms == expected


def test_insert(io, ethanol):
    for i, atom in enumerate(ethanol):
        io[i] = asebytes.to_bytes(atom)
    new_atom = asebytes.to_bytes(ethanol[0])
    io.insert(1, new_atom)
    assert len(io) == len(ethanol) + 1
    atoms = [asebytes.from_bytes(io[i]) for i in range(len(io))]
    expected = [ethanol[0], ethanol[0]] + ethanol[1:]
    assert atoms == expected


def test_iter(io, ethanol):
    for i, atom in enumerate(ethanol):
        io[i] = asebytes.to_bytes(atom)
    atoms = [asebytes.from_bytes(data) for data in io]
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
