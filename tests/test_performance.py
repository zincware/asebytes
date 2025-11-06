import asebytes
import tempfile
import time
import pytest

def test_insert_performance():
    """Verify that insert doesn't shift data (should be fast even with many items)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        io = asebytes.BytesIO(f"{tmpdir}/perf.db")

        # Add 1000 items
        test_data = {b"test": b"x" * 100}
        for i in range(1000):
            io[i] = test_data

        # Time insert at beginning (worst case)
        start = time.time()
        io.insert(0, test_data)
        elapsed = time.time() - start

        # Should be fast (< 100ms even with 1000 items)
        # Old implementation would take seconds
        assert elapsed < 0.1, f"Insert took {elapsed:.3f}s, expected < 0.1s"
        assert len(io) == 1001

def test_delete_performance():
    """Verify that delete doesn't shift data"""
    with tempfile.TemporaryDirectory() as tmpdir:
        io = asebytes.BytesIO(f"{tmpdir}/perf.db")

        # Add 1000 items
        test_data = {b"test": b"x" * 100}
        for i in range(1000):
            io[i] = test_data

        # Time delete at beginning (worst case)
        start = time.time()
        del io[0]
        elapsed = time.time() - start

        # Should be fast (< 100ms even with 1000 items)
        assert elapsed < 0.1, f"Delete took {elapsed:.3f}s, expected < 0.1s"
        assert len(io) == 999

def test_len_performance():
    """Verify that len is O(1)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        io = asebytes.BytesIO(f"{tmpdir}/perf.db")

        # Add 1000 items
        test_data = {b"test": b"x" * 100}
        for i in range(1000):
            io[i] = test_data

        # Time 10000 len() calls
        start = time.time()
        for _ in range(10000):
            _ = len(io)
        elapsed = time.time() - start

        # Should be very fast (< 100ms for 10000 calls)
        assert elapsed < 0.1, f"10000 len() calls took {elapsed:.3f}s"
