from dataclasses import dataclass

import numpy as np

@dataclass
class Keypad:
    keypad: np.ndarray
    k: int # number of keys
    p: int  # properties per key
    keypad_cache: list
    max_cache_size: int = 100

    @staticmethod
    def new_keypad(k: int, p: int):
        total_properties = k * p
        array = np.arange(total_properties)
        # Reshape into a 3x4 matrix
        keypad = array.reshape(k, p)
        set_view = keypad.T

        for set_idx in set_view:
            np.random.shuffle(set_idx)

        return Keypad(keypad=set_view.T, k=k, p=p, keypad_cache=[])

    def split_shuffle(self):
        shuffled_sets = self._shuffle()
        sorted_set = shuffled_sets[np.argsort(shuffled_sets[:, 0])]

        while str(sorted_set) in self.keypad_cache:
            shuffled_sets = self._shuffle()
            sorted_set = shuffled_sets[np.argsort(shuffled_sets[:, 0])]

        self.keypad_cache.append(str(sorted_set))
        self.keypad_cache = self.keypad_cache[:self.max_cache_size]

        self.keypad = shuffled_sets


    def _shuffle(self) -> np.ndarray:
        column_permutation = np.random.permutation(self.p)
        column_subset = column_permutation[:self.p // 2]
        perm_indices = np.random.permutation(self.k)
        shuffled_sets = self.keypad.copy()
        shuffled_sets[:, column_subset] = shuffled_sets[perm_indices, :][:, column_subset]
        return shuffled_sets

    def full_shuffle(self):
        shuffled_matrix = np.array([np.random.permutation(row) for row in self.keypad.T])
        self.keypad = shuffled_matrix.T

    def key_entry(self, target_passcode: list[int]) -> list[int]:
        """
        Given target_values, return the row indices they are in.
        Assert that each element is >= 0 and < self.k * self.p.
        """
        # Convert the list to a NumPy array for vectorized checks
        vals = np.array(target_passcode)

        # Validate that each value is within the valid range
        if np.any((vals < 0) | (vals >= self.k * self.p)):
            raise ValueError("One or more values are out of the valid range.")

        # Flatten the keypad to a 1D array
        flat = self.keypad.flatten()

        # Create an inverse mapping from value -> row index
        inv_index = np.empty(self.k * self.p, dtype=int)
        # Each value v is at position i in 'flat', so row = i // p
        for i, v in enumerate(flat):
            inv_index[v] = i // self.p

        # Use the inverse mapping to get row indices for all target values
        return inv_index[vals].tolist()
