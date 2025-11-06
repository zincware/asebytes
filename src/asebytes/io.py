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

    def __setitem__(self, index: int, data: dict[bytes, bytes]) -> None:
        with self.env.begin(write=True) as txn:
            # First, remove all existing keys for this index
            cursor = txn.cursor()
            prefix = self.prefix + str(index).encode() + b"-"
            keys_to_delete = []
            if cursor.set_range(prefix):
                for key, value in cursor:
                    if not key.startswith(prefix):
                        break
                    keys_to_delete.append(key)

            # Delete all old keys
            for key in keys_to_delete:
                txn.delete(key)

            # Write new data
            for key, value in data.items():
                txn.put(self.prefix + str(index).encode() + b"-" + key, value)

    def __getitem__(self, index: int) -> dict[bytes, bytes]:
        result = {}
        with self.env.begin() as txn:
            cursor = txn.cursor()
            prefix = self.prefix + str(index).encode() + b"-"
            if cursor.set_range(prefix):
                for key, value in cursor:
                    if not key.startswith(prefix):
                        break
                    result[key[len(prefix):]] = value
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
        count = 0
        with self.env.begin() as txn:
            cursor = txn.cursor()
            prefix = self.prefix
            if cursor.first():
                for key, value in cursor:
                    if not key.startswith(prefix):
                        continue
                    index_str = key[len(prefix):].split(b"-", 1)[0]
                    index = int(index_str)
                    if index + 1 > count:
                        count = index + 1
        return count
    


    