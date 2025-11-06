from collections.abc import MutableSequence
from typing import Iterator

import ase
import lmdb

from asebytes.from_bytes import from_bytes
from asebytes.to_bytes import to_bytes


class ASEIO(MutableSequence):
    def __init__(self, file: str, prefix: bytes = b""):
        self.io = BytesIO(file, prefix)

    def __getitem__(self, index: int) -> ase.Atoms:
        data = self.io[index]
        return from_bytes(data)

    def __setitem__(self, index: int, value: ase.Atoms) -> None:
        data = to_bytes(value)
        self.io[index] = data

    def __delitem__(self, index: int) -> None:
        del self.io[index]

    def insert(self, index: int, value: ase.Atoms) -> None:
        data = to_bytes(value)
        self.io.insert(index, data)

    def __len__(self) -> int:
        return len(self.io)

    def __iter__(self) -> Iterator:
        for i in range(len(self)):
            yield self[i]

    def get(self, index: int, keys: list[bytes] | None = None) -> ase.Atoms:
        """Get Atoms object at index, optionally filtering to specific keys.

        Args:
            index: The logical index to retrieve
            keys: Optional list of keys to retrieve. If None, returns all data.
                  Keys should be in the format used internally (e.g., b"arrays.positions",
                  b"info.smiles", b"calc.energy")

        Returns:
            ase.Atoms object reconstructed from the requested keys

        Raises:
            KeyError: If the index does not exist
        """
        data = self.io.get(index, keys=keys)
        return from_bytes(data)


class BytesIO(MutableSequence):
    def __init__(self, file: str, prefix: bytes = b""):
        self.file = file
        self.prefix = prefix
        self.env = lmdb.open(
            file,
            # map_size=1099511627776,
            # subdir=False,
            # readonly=False,
            # lock=True,
            # readahead=True,
            # meminit=False,
        )

    # Metadata helpers
    def _get_count(self, txn) -> int:
        """Get the current count from metadata. Returns 0 if not set."""
        count_key = self.prefix + b"__meta__count"
        count_bytes = txn.get(count_key)
        if count_bytes is None:
            return 0
        return int(count_bytes.decode())

    def _set_count(self, txn, count: int) -> None:
        """Set the count in metadata."""
        count_key = self.prefix + b"__meta__count"
        txn.put(count_key, str(count).encode())

    def _get_next_sort_key(self, txn) -> int:
        """Get the next available sort key counter. Returns 0 if not set."""
        key = self.prefix + b"__meta__next_sort_key"
        value = txn.get(key)
        if value is None:
            return 0
        return int(value.decode())

    def _set_next_sort_key(self, txn, value: int) -> None:
        """Set the next available sort key counter."""
        key = self.prefix + b"__meta__next_sort_key"
        txn.put(key, str(value).encode())

    # Mapping helpers (logical_index → sort_key)
    def _get_mapping(self, txn, logical_index: int) -> int | None:
        """Get sort_key for a logical index. Returns None if not found."""
        mapping_key = self.prefix + b"__idx__" + str(logical_index).encode()
        sort_key_bytes = txn.get(mapping_key)
        if sort_key_bytes is None:
            return None
        return int(sort_key_bytes.decode())

    def _set_mapping(self, txn, logical_index: int, sort_key: int) -> None:
        """Set the mapping from logical_index to sort_key."""
        mapping_key = self.prefix + b"__idx__" + str(logical_index).encode()
        txn.put(mapping_key, str(sort_key).encode())

    def _delete_mapping(self, txn, logical_index: int) -> None:
        """Delete the mapping for a logical index."""
        mapping_key = self.prefix + b"__idx__" + str(logical_index).encode()
        txn.delete(mapping_key)

    def _allocate_sort_key(self, txn) -> int:
        """Allocate a new unique sort key by incrementing the counter."""
        next_key = self._get_next_sort_key(txn)
        self._set_next_sort_key(txn, next_key + 1)
        return next_key

    def __setitem__(self, index: int, data: dict[bytes, bytes]) -> None:
        with self.env.begin(write=True) as txn:
            current_count = self._get_count(txn)

            # Get or allocate sort key for this index
            sort_key = self._get_mapping(txn, index)
            is_new_index = sort_key is None

            if is_new_index:
                # Allocate new unique sort key
                sort_key = self._allocate_sort_key(txn)
                self._set_mapping(txn, index, sort_key)

            # Delete existing data keys with this sort key
            cursor = txn.cursor()
            sort_key_str = str(sort_key).encode()
            prefix = self.prefix + sort_key_str + b"-"
            keys_to_delete = []

            if cursor.set_range(prefix):
                for key, value in cursor:
                    if not key.startswith(prefix):
                        break
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                txn.delete(key)

            # Write new data with sort key prefix using putmulti
            items_to_insert = [
                (self.prefix + sort_key_str + b"-" + key, value)
                for key, value in data.items()
            ]
            if items_to_insert:
                cursor.putmulti(items_to_insert, dupdata=False)

            # Update count if needed (when index == current_count, we're appending)
            if is_new_index and index >= current_count:
                self._set_count(txn, index + 1)

    def __getitem__(self, index: int) -> dict[bytes, bytes]:
        with self.env.begin() as txn:
            # Look up the sort key for this logical index
            sort_key = self._get_mapping(txn, index)

            if sort_key is None:
                raise KeyError(f"Index {index} not found")

            # Scan for all data keys with this sort key prefix
            result = {}
            cursor = txn.cursor()
            sort_key_str = str(sort_key).encode()
            prefix = self.prefix + sort_key_str + b"-"

            if cursor.set_range(prefix):
                for key, value in cursor:
                    if not key.startswith(prefix):
                        break
                    # Extract the field name after the sort_key prefix
                    field_name = key[len(prefix) :]
                    result[field_name] = value

            return result

    def get(self, index: int, keys: list[bytes] | None = None) -> dict[bytes, bytes]:
        """Get data at index, optionally filtering to specific keys.

        Args:
            index: The logical index to retrieve
            keys: Optional list of keys to retrieve. If None, returns all keys.

        Returns:
            Dictionary of key-value pairs. If keys is provided, only those keys
            that exist in the data are returned.

        Raises:
            KeyError: If the index does not exist
        """
        with self.env.begin() as txn:
            # Look up the sort key for this logical index
            sort_key = self._get_mapping(txn, index)

            if sort_key is None:
                raise KeyError(f"Index {index} not found")

            # Scan for all data keys with this sort key prefix
            result = {}
            cursor = txn.cursor()
            sort_key_str = str(sort_key).encode()
            prefix = self.prefix + sort_key_str + b"-"

            # Convert keys to a set for fast lookup
            keys_set = set(keys) if keys is not None else None

            if cursor.set_range(prefix):
                for key, value in cursor:
                    if not key.startswith(prefix):
                        break
                    # Extract the field name after the sort_key prefix
                    field_name = key[len(prefix) :]

                    # If keys filter is specified, only include requested keys
                    if keys_set is None or field_name in keys_set:
                        result[field_name] = value

            return result

    def __delitem__(self, key: int) -> None:
        with self.env.begin(write=True) as txn:
            current_count = self._get_count(txn)

            if key < 0 or key >= current_count:
                raise IndexError(f"Index {key} out of range [0, {current_count})")

            # Get the sort key for this index
            sort_key = self._get_mapping(txn, key)
            if sort_key is None:
                raise KeyError(f"Index {key} not found")

            # Collect all mappings that need to be shifted
            # We need to shift indices [key+1, key+2, ..., count-1] down by 1
            mappings_to_shift = []
            for i in range(key + 1, current_count):
                sk = self._get_mapping(txn, i)
                if sk is not None:
                    mappings_to_shift.append((i, sk))

            # Delete the mapping for the deleted index
            self._delete_mapping(txn, key)

            # Shift all subsequent mappings down by 1
            # Delete old mappings first, then write new ones
            for old_index, sk in mappings_to_shift:
                self._delete_mapping(txn, old_index)

            for old_index, sk in mappings_to_shift:
                new_index = old_index - 1
                self._set_mapping(txn, new_index, sk)

            # Optionally delete the data keys (lazy deletion strategy)
            # For now, we'll delete them to keep the database clean
            cursor = txn.cursor()
            sort_key_str = str(sort_key).encode()
            prefix = self.prefix + sort_key_str + b"-"
            keys_to_delete = []

            if cursor.set_range(prefix):
                for k, value in cursor:
                    if not k.startswith(prefix):
                        break
                    keys_to_delete.append(k)

            for k in keys_to_delete:
                txn.delete(k)

            # Update count
            self._set_count(txn, current_count - 1)

    def insert(self, index: int, input: dict[bytes, bytes]) -> None:
        with self.env.begin(write=True) as txn:
            current_count = self._get_count(txn)

            # Clamp index to valid range [0, count]
            if index < 0:
                index = 0
            if index > current_count:
                index = current_count

            # Collect all mappings that need to be shifted right
            # We need to shift indices [index, index+1, ..., count-1] up by 1
            mappings_to_shift = []
            for i in range(index, current_count):
                sk = self._get_mapping(txn, i)
                if sk is not None:
                    mappings_to_shift.append((i, sk))

            # Shift all mappings up by 1
            # Do this in reverse order to avoid conflicts
            # Delete old mappings first, then write new ones
            for old_index, sk in mappings_to_shift:
                self._delete_mapping(txn, old_index)

            for old_index, sk in reversed(mappings_to_shift):
                new_index = old_index + 1
                self._set_mapping(txn, new_index, sk)

            # Allocate a new sort key for the new item
            sort_key = self._allocate_sort_key(txn)
            self._set_mapping(txn, index, sort_key)

            # Write the new data with sort key prefix using putmulti
            sort_key_str = str(sort_key).encode()
            items_to_insert = [
                (self.prefix + sort_key_str + b"-" + key, value)
                for key, value in input.items()
            ]
            if items_to_insert:
                cursor = txn.cursor()
                cursor.putmulti(items_to_insert, dupdata=False)

            # Update count
            self._set_count(txn, current_count + 1)

    def extend(self, items: list[dict[bytes, bytes]]) -> None:
        """Efficiently extend the sequence with multiple items using bulk operations."""
        if not items:
            return

        with self.env.begin(write=True) as txn:
            current_count = self._get_count(txn)

            # Prepare all items with their mappings and data keys
            items_to_insert = []

            for idx, item in enumerate(items):
                logical_index = current_count + idx
                sort_key = self._allocate_sort_key(txn)

                # Add mapping entry
                mapping_key = self.prefix + b"__idx__" + str(logical_index).encode()
                items_to_insert.append((mapping_key, str(sort_key).encode()))

                # Add data entries for each field
                sort_key_str = str(sort_key).encode()
                for field_key, field_value in item.items():
                    data_key = self.prefix + sort_key_str + b"-" + field_key
                    items_to_insert.append((data_key, field_value))

            # Bulk insert all items
            cursor = txn.cursor()
            cursor.putmulti(items_to_insert, dupdata=False)

            # Update count
            self._set_count(txn, current_count + len(items))

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __len__(self) -> int:
        with self.env.begin() as txn:
            return self._get_count(txn)
