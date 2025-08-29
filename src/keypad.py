from dataclasses import dataclass

import numpy as np

from src.tower_shuffle import TowerShuffle


@dataclass
class Keypad:
    keypad: np.ndarray
    k: int # number of keys
    p: int  # properties per key
    keypad_cache: list #
    tower_shuffler: TowerShuffle
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

        return Keypad(keypad=set_view.T, k=k, p=p, keypad_cache=[], tower_shuffler=TowerShuffle.new(p))

    def tower_shuffle(self):
        selected_positions = self.tower_shuffler.left_tower.tolist()
        new_key_idxs = np.random.permutation(self.k)
        self.keypad[:, selected_positions] = self.keypad[new_key_idxs, :][:, selected_positions]
        self.tower_shuffler.shuffle()

    def split_shuffle(self):
        """
        This is a modified split shuffle.
        It doesn't shuffle the keys only the properties in the keys.
        Shuffling the keys makes it hard for people to guess an nKode not a machine.
        This split shuffle includes a cache to prevent the same configuration from being used.
        This cache is not in any other implementation.
        Testing suggests it's not necessary.
        Getting the same keypad twice over 100 shuffles is very unlikely.
        """
        shuffled_sets = self._shuffle()
        # Sort the shuffled sets by the first column
        sorted_set = shuffled_sets[np.argsort(shuffled_sets[:, 0])]
        while str(sorted_set) in self.keypad_cache:
            # continue shuffling until we get a unique configuration
            shuffled_sets = self._shuffle()
            sorted_set = shuffled_sets[np.argsort(shuffled_sets[:, 0])]

        self.keypad_cache.append(str(sorted_set))
        self.keypad_cache = self.keypad_cache[:self.max_cache_size]
        self.keypad = shuffled_sets


    def _shuffle(self) -> np.ndarray:
        column_permutation = np.random.permutation(self.p)
        column_subset = column_permutation[:self.p // 2]
        new_key_idxs = np.random.permutation(self.k)
        shuffled_sets = self.keypad.copy()
        shuffled_sets[:, column_subset] = shuffled_sets[new_key_idxs, :][:, column_subset]
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
