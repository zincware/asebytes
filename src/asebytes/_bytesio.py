from collections.abc import MutableSequence

import lmdb


class BytesIO(MutableSequence):
    """
    LMDB-backed mutable sequence for byte dictionaries.

    Parameters
    ----------
    file : str
        Path to LMDB database file.
    prefix : bytes, default=b""
        Key prefix for namespacing entries.
    map_size : int, default=10737418240
        Maximum size of the LMDB database in bytes (default 10GB).
    readonly : bool, default=False
        If True, opens database in read-only mode.
    **lmdb_kwargs
        Additional keyword arguments passed to lmdb.open().
    """

    def __init__(
        self,
        file: str,
        prefix: bytes = b"",
        map_size: int = 10737418240,
        readonly: bool = False,
        **lmdb_kwargs,
    ):
        self.file = file
        self.prefix = prefix
        self.env = lmdb.open(
            file,
            map_size=map_size,
            subdir=False,
            readonly=readonly,
            **lmdb_kwargs,
        )

    # Metadata helpers
    def _get_count(self, txn) -> int:
        """Get the current count from metadata (returns 0 if not set)."""
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
        """Get the next available sort key counter (returns 0 if not set)."""
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
        """Get sort_key for a logical index (returns None if not found)."""
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

    # Metadata helpers for field keys
    def _get_field_keys_metadata(self, txn, sort_key: int) -> list[bytes] | None:
        """
        Get field keys for a sort key from metadata.

        Parameters
        ----------
        txn : lmdb.Transaction
            LMDB transaction.
        sort_key : int
            Sort key to query.

        Returns
        -------
        list[bytes] or None
            Field keys (without prefix) or None if not found.
        """
        metadata_key = self.prefix + b"__keys__" + str(sort_key).encode()
        metadata_bytes = txn.get(metadata_key)
        if metadata_bytes is None:
            return None
        # Deserialize the list of keys (stored as newline-separated bytes)
        return metadata_bytes.split(b"\n") if metadata_bytes else []

    def _set_field_keys_metadata(
        self, txn, sort_key: int, field_keys: list[bytes]
    ) -> None:
        """
        Store field keys for a sort key in metadata.

        Parameters
        ----------
        txn : lmdb.Transaction
            LMDB transaction.
        sort_key : int
            Sort key.
        field_keys : list[bytes]
            Field keys (without prefix).
        """
        metadata_key = self.prefix + b"__keys__" + str(sort_key).encode()
        # Serialize as newline-separated bytes
        metadata_bytes = b"\n".join(field_keys)
        txn.put(metadata_key, metadata_bytes)

    def _delete_field_keys_metadata(self, txn, sort_key: int) -> None:
        """
        Delete field keys metadata for a sort key.

        Parameters
        ----------
        txn : lmdb.Transaction
            LMDB transaction.
        sort_key : int
            Sort key.
        """
        metadata_key = self.prefix + b"__keys__" + str(sort_key).encode()
        txn.delete(metadata_key)

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
            else:
                # Delete existing data keys if overwriting
                try:
                    _, _, keys_to_delete = self._get_full_keys(txn, index)
                    for key in keys_to_delete:
                        txn.delete(key)
                except KeyError:
                    # No existing data, continue
                    pass

            # Write new data with sort key prefix using putmulti
            sort_key_str = str(sort_key).encode()
            items_to_insert = [
                (self.prefix + sort_key_str + b"-" + key, value)
                for key, value in data.items()
            ]
            if items_to_insert:
                cursor = txn.cursor()
                cursor.putmulti(items_to_insert, dupdata=False)

            # Store metadata for field keys
            field_keys = list(data.keys())
            self._set_field_keys_metadata(txn, sort_key, field_keys)

            # Update count if needed (when index == current_count, we're appending)
            if is_new_index and index >= current_count:
                self._set_count(txn, index + 1)

    def _get_full_keys(self, txn, index: int) -> tuple[int, bytes, list[bytes]]:
        """
        Get sort key, prefix, and all full keys for an index.

        Parameters
        ----------
        txn : lmdb.Transaction
            LMDB transaction.
        index : int
            Logical index to query.

        Returns
        -------
        tuple[int, bytes, list[bytes]]
            Tuple of (sort_key, prefix, full keys including prefix).

        Raises
        ------
        KeyError
            If the index does not exist.
        """
        # Look up the sort key for this logical index
        sort_key = self._get_mapping(txn, index)

        if sort_key is None:
            raise KeyError(f"Index {index} not found")

        # Build prefix
        sort_key_str = str(sort_key).encode()
        prefix = self.prefix + sort_key_str + b"-"

        # Get field keys from metadata
        field_keys = self._get_field_keys_metadata(txn, sort_key)
        if field_keys is None:
            raise KeyError(
                f"Metadata not found for index {index} (sort_key {sort_key})"
            )

        # Build full keys with prefix
        keys_to_fetch = [prefix + field_key for field_key in field_keys]

        return sort_key, prefix, keys_to_fetch

    def __getitem__(self, index: int) -> dict[bytes, bytes]:
        with self.env.begin() as txn:
            _, prefix, keys_to_fetch = self._get_full_keys(txn, index)

            # Use getmulti for efficient batch retrieval
            result = {}
            if keys_to_fetch:
                cursor = txn.cursor()
                for key, value in cursor.getmulti(keys_to_fetch):
                    # Extract the field name after the sort_key prefix
                    field_name = key[len(prefix) :]
                    result[field_name] = value

            return result

    def get_available_keys(self, index: int) -> list[bytes]:
        """
        Get all available keys for a given index.

        Parameters
        ----------
        index : int
            Logical index to query.

        Returns
        -------
        list[bytes]
            Available keys at the index.

        Raises
        ------
        KeyError
            If the index does not exist.
        """
        with self.env.begin() as txn:
            _, prefix, keys_to_fetch = self._get_full_keys(txn, index)

            # Extract field names from full keys
            return [key[len(prefix) :] for key in keys_to_fetch]

    def get_with_txn(self, txn, index: int, keys: list[bytes] | None = None) -> dict[bytes, bytes]:
        """
        Get data at index using an existing LMDB transaction.

        Same as get() but accepts an external transaction for batched reads
        within a single transaction scope.

        Parameters
        ----------
        txn : lmdb.Transaction
            An active LMDB read transaction.
        index : int
            Logical index to retrieve.
        keys : list[bytes], optional
            Keys to retrieve. If None, returns all keys.

        Returns
        -------
        dict[bytes, bytes]
            Key-value pairs.
        """
        _, prefix, keys_to_fetch = self._get_full_keys(txn, index)

        keys_set = None
        if keys is not None:
            keys_set = set(keys)
            keys_to_fetch = [prefix + field_key for field_key in keys_set]

        result = {}
        if keys_to_fetch:
            cursor = txn.cursor()
            for key, value in cursor.getmulti(keys_to_fetch):
                field_name = key[len(prefix) :]
                result[field_name] = value

        if keys_set is not None and len(result) != len(keys_set):
            retrieved_keys = set(result.keys())
            invalid_keys = keys_set - retrieved_keys
            raise KeyError(f"Invalid keys at index {index}: {sorted(invalid_keys)}")

        return result

    def get(self, index: int, keys: list[bytes] | None = None) -> dict[bytes, bytes]:
        """
        Get data at index, optionally filtering to specific keys.

        Parameters
        ----------
        index : int
            Logical index to retrieve.
        keys : list[bytes], optional
            Keys to retrieve. If None, returns all keys.

        Returns
        -------
        dict[bytes, bytes]
            Key-value pairs. If keys provided, only existing keys are returned.

        Raises
        ------
        KeyError
            If the index does not exist or if any of the requested keys are not found.
        """
        with self.env.begin() as txn:
            return self.get_with_txn(txn, index, keys)

    def update(self, index: int, data: dict[bytes, bytes]) -> None:
        """
        Update or add specific keys to an existing entry without overwriting all data.

        This method performs an atomic update of specific keys at the given index.
        All updates succeed or fail together as a single transaction.

        Parameters
        ----------
        index : int
            Index of the entry to update.
        data : dict[bytes, bytes]
            Dictionary of keys to add/update. Keys are field names (e.g., b"info.s22"),
            values must be msgpack-encoded bytes.

        Raises
        ------
        KeyError
            If the index does not exist.

        Examples
        --------
        >>> import msgpack
        >>> import msgpack_numpy as m
        >>> db = BytesIO("molecules.lmdb")
        >>> # Add new keys to existing entry
        >>> db.update(0, {
        ...     b"info.s22": msgpack.packb(123.45, default=m.encode),
        ...     b"info.connectivity": msgpack.packb([[0,1],[1,2]], default=m.encode)
        ... })
        """
        # Empty dict is a no-op
        if not data:
            return

        with self.env.begin(write=True) as txn:
            # Verify index exists
            sort_key = self._get_mapping(txn, index)
            if sort_key is None:
                raise KeyError(f"Index {index} not found")

            # Get existing field keys to update metadata later
            existing_field_keys = self._get_field_keys_metadata(txn, sort_key)
            if existing_field_keys is None:
                existing_field_keys = []

            # Build the set of all field keys (existing + new)
            new_field_keys = set(data.keys())
            all_field_keys = set(existing_field_keys) | new_field_keys

            # Build full keys with prefix and perform atomic multiset
            sort_key_str = str(sort_key).encode()
            prefix = self.prefix + sort_key_str + b"-"

            items_to_update = [
                (prefix + field_key, value) for field_key, value in data.items()
            ]

            # Atomic put: all keys updated or none
            if items_to_update:
                cursor = txn.cursor()
                cursor.putmulti(items_to_update, dupdata=False, overwrite=True)

            # Update metadata with complete field key list
            self._set_field_keys_metadata(txn, sort_key, sorted(all_field_keys))

    def __delitem__(self, key: int) -> None:
        with self.env.begin(write=True) as txn:
            current_count = self._get_count(txn)

            if key < 0:
                key += current_count
            if key < 0 or key >= current_count:
                raise IndexError(f"Index {key} out of range [0, {current_count})")

            # Get the sort key for this index and data keys before deleting mapping
            sort_key = self._get_mapping(txn, key)
            if sort_key is None:
                raise KeyError(f"Index {key} not found")

            # Get the data keys to delete before modifying mappings
            _, _, keys_to_delete = self._get_full_keys(txn, key)

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

            # Delete the data keys
            for k in keys_to_delete:
                txn.delete(k)

            # Delete metadata for field keys
            self._delete_field_keys_metadata(txn, sort_key)

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

            # Store metadata for field keys
            field_keys = list(input.keys())
            self._set_field_keys_metadata(txn, sort_key, field_keys)

            # Update count
            self._set_count(txn, current_count + 1)

    def extend(self, items: list[dict[bytes, bytes]]) -> None:
        """
        Efficiently extend the sequence with multiple items using bulk operations.

        Parameters
        ----------
        items : list[dict[bytes, bytes]]
            Dictionaries to append.
        """
        if not items:
            return

        with self.env.begin(write=True) as txn:
            current_count = self._get_count(txn)

            # Prepare all items with their mappings, data keys, and metadata
            items_to_insert = []

            for idx, item in enumerate(items):
                logical_index = current_count + idx
                sort_key = self._allocate_sort_key(txn)
                sort_key_str = str(sort_key).encode()

                # Add mapping entry
                mapping_key = self.prefix + b"__idx__" + str(logical_index).encode()
                items_to_insert.append((mapping_key, sort_key_str))

                # Collect field keys and add data entries
                field_keys = list(item.keys())
                for field_key, field_value in item.items():
                    data_key = self.prefix + sort_key_str + b"-" + field_key
                    items_to_insert.append((data_key, field_value))

                # Add metadata entry (inline with other inserts for single putmulti)
                metadata_key = self.prefix + b"__keys__" + sort_key_str
                metadata_value = b"\n".join(field_keys)
                items_to_insert.append((metadata_key, metadata_value))

            # Bulk insert all items (mappings + data + metadata) in one call
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
