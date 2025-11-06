from collections.abc import MutableSequence
import lmdb

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

            # Write new data with sort key prefix
            for key, value in data.items():
                txn.put(self.prefix + sort_key_str + b"-" + key, value)

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
                    field_name = key[len(prefix):]
                    result[field_name] = value

            return result
    
    def __delitem__(self, key: int) -> None:
        with self.env.begin(write=True) as txn:
            # remove the item and shift all subsequent items one position to the left
            cursor = txn.cursor()
            keys_to_move = []
            prefix = self.prefix + str(key).encode() + b"-"
            if cursor.set_range(prefix):
                for k, value in cursor:
                    if not k.startswith(self.prefix):
                        break
                    index_str = k[len(self.prefix):].split(b"-", 1)[0]
                    current_index = int(index_str)
                    if current_index >= key:
                        keys_to_move.append((k, value))
            for k, value in keys_to_move:
                index_str = k[len(self.prefix):].split(b"-", 1)[0]
                current_index = int(index_str)
                if current_index == key:
                    txn.delete(k)
                else:
                    new_key = self.prefix + str(current_index - 1).encode() + b"-" + k[len(self.prefix) + len(index_str) + 1:]
                    txn.put(new_key, value)
                    txn.delete(k)

    def insert(self, index: int, input: dict[bytes, bytes]) -> None:
        with self.env.begin(write=True) as txn:
            # move all items from index to end one position to the right
            cursor = txn.cursor()
            keys_to_move = []
            prefix = self.prefix + str(index).encode() + b"-"
            if cursor.set_range(prefix):
                for key, value in cursor:
                    if not key.startswith(self.prefix):
                        break
                    index_str = key[len(self.prefix):].split(b"-", 1)[0]
                    current_index = int(index_str)
                    if current_index >= index:
                        keys_to_move.append((key, value))
            for key, value in reversed(keys_to_move):
                index_str = key[len(self.prefix):].split(b"-", 1)[0]
                current_index = int(index_str)
                new_key = self.prefix + str(current_index + 1).encode() + b"-" + key[len(self.prefix) + len(index_str) + 1:]
                txn.put(new_key, value)
                txn.delete(key)
            # insert the new value
            for key, value in input.items():
                txn.put(self.prefix + str(index).encode() + b"-" + key, value)
    
    def __iter__(self):
        for i in range(len(self)):
            yield self[i]
    
    def __len__(self) -> int:
        with self.env.begin() as txn:
            return self._get_count(txn)
    


    