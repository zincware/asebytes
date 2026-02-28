import msgpack
import msgpack_numpy as m
import numpy as np
import pytest
from asebytes._backends import ReadBackend


def _pack(v):
    return msgpack.packb(v, default=m.encode)


def _unpack(v):
    return msgpack.unpackb(v, object_hook=m.decode)


def test_uni_blob_isinstance(uni_blob_backend):
    assert isinstance(uni_blob_backend, ReadBackend)


def test_uni_blob_empty_len(uni_blob_backend):
    assert len(uni_blob_backend) == 0


def test_uni_blob_extend_get(uni_blob_backend):
    rows = [
        {b"calc.energy": _pack(-1.0), b"info.smiles": _pack("O")},
        {b"calc.energy": _pack(-2.0), b"info.smiles": _pack("CC")},
    ]
    uni_blob_backend.extend(rows)
    assert len(uni_blob_backend) == 2
    row = uni_blob_backend.get(0)
    assert _unpack(row[b"calc.energy"]) == pytest.approx(-1.0)
    assert _unpack(row[b"info.smiles"]) == "O"


def test_uni_blob_none_placeholder(uni_blob_backend):
    uni_blob_backend.extend([{b"a": _pack(1)}, None, {b"a": _pack(3)}])
    assert uni_blob_backend.get(1) is None


def test_uni_blob_numpy_roundtrip(uni_blob_backend):
    arr = np.array([[1.0, 2.0], [3.0, 4.0]])
    row = {b"calc.data": _pack(arr)}
    uni_blob_backend.extend([row])
    result = uni_blob_backend.get(0)
    assert np.allclose(_unpack(result[b"calc.data"]), arr)
