from dataclasses import dataclass, field
import numpy as np
from src.keypad.tower_shuffle import TowerShuffle
from abc import ABC, abstractmethod
from typing import Self, Sequence


class BaseKeypad(ABC):
    keypad: np.ndarray
    k: int  # number of keys
    p: int  # properties per key

    @classmethod
    def _build_keypad(
        cls,
        k: int,
        p: int,
        rng: np.random.Generator,
    ) -> np.ndarray:
        total = k * p
        array = np.arange(total)
        keypad = array.reshape(k, p)
        set_view = keypad.T.copy()
        for set_idx in set_view:
            rng.shuffle(set_idx)
        return set_view.T

    @classmethod
    @abstractmethod
    def new_keypad(
        cls,
        k: int,
        p: int,
        rng: np.random.Generator | None = None,
    ) -> Self:
        raise NotImplementedError

    def key_entry(self, target_passcode: list[int]) -> list[int]:
        vals = np.array(target_passcode)
        if np.any((vals < 0) | (vals >= self.k * self.p)):
            raise ValueError("One or more values are out of the valid range.")
        flat = self.keypad.flatten()
        inv_index = np.empty(self.k * self.p, dtype=int)
        for i, v in enumerate(flat):
            inv_index[v] = i // self.p
        return inv_index[vals].tolist()

    @abstractmethod
    def shuffle(self):
        pass

    def keypad_mat(self) -> list[list[int]]:
        return [el.tolist() for el in self.keypad]


@dataclass
class SlidingTowerShuffleKeypad(BaseKeypad):
    keypad: np.ndarray
    k: int  # number of keys
    p: int  # properties per key
    tower_shuffle: TowerShuffle
    rng: np.random.Generator = field(
        default_factory=np.random.default_rng,
        repr=False,
        compare=False,
    )

    @classmethod
    def new_keypad(
        cls,
        k: int,
        p: int,
        rng: np.random.Generator | None = None,
    ) -> Self:
        if rng is None:
            rng = np.random.default_rng()
        kp = cls._build_keypad(k, p, rng)
        return cls(
            keypad=kp,
            k=k,
            p=p,
            tower_shuffle=TowerShuffle.new(p, rng),
            rng=rng,
        )

    def shuffle(self):
        selected_positions = self.tower_shuffle.left_tower.tolist()
        shifts = self.rng.permutation(np.arange(1, self.k))[:2]
        set_view = self.keypad.T.copy()
        for idx, icon_set in enumerate(set_view):
            shift = shifts[0] if idx in selected_positions else shifts[1]
            set_view[idx] = np.roll(icon_set, shift)
        self.keypad = set_view.T
        self.tower_shuffle.shuffle()


@dataclass(frozen=True)
class SelectiveShuffleResult:
    pressed_keys: tuple[int, ...]
    rotation_keys: tuple[int, ...]
    left_shift: int
    right_shift: int
    moved_icons: int
    fixed_columns: tuple[int, ...]


def _child_rng(rng: np.random.Generator) -> np.random.Generator:
    seed = int(rng.integers(0, np.iinfo(np.int64).max))
    return np.random.default_rng(seed)


@dataclass
class SelectiveTowerShuffleKeypad(BaseKeypad):
    keypad: np.ndarray
    k: int
    p: int
    tower_shuffle: TowerShuffle
    extra_key_rng: np.random.Generator = field(
        default_factory=np.random.default_rng,
        repr=False,
        compare=False,
    )
    rotation_rng: np.random.Generator = field(
        default_factory=np.random.default_rng,
        repr=False,
        compare=False,
    )
    tower_floor_rng: np.random.Generator = field(
        default_factory=np.random.default_rng,
        repr=False,
        compare=False,
    )

    @classmethod
    def new_keypad(
        cls,
        k: int,
        p: int,
        rng: np.random.Generator | None = None,
        tower_init_rng: np.random.Generator | None = None,
        extra_key_rng: np.random.Generator | None = None,
        rotation_rng: np.random.Generator | None = None,
        tower_floor_rng: np.random.Generator | None = None,
    ) -> Self:
        if k < 2:
            raise ValueError("selective tower shuffle requires at least 2 keys")
        if p < 3:
            raise ValueError(
                "selective tower shuffle requires at least 3 icon columns"
            )
        if rng is None:
            rng = np.random.default_rng()
        keypad = cls._build_keypad(k, p, rng)
        if tower_init_rng is None:
            tower_init_rng = _child_rng(rng)
        if extra_key_rng is None:
            extra_key_rng = _child_rng(rng)
        if rotation_rng is None:
            rotation_rng = _child_rng(rng)
        if tower_floor_rng is None:
            tower_floor_rng = _child_rng(rng)
        return cls(
            keypad=keypad,
            k=k,
            p=p,
            tower_shuffle=TowerShuffle.new(p, tower_init_rng),
            extra_key_rng=extra_key_rng,
            rotation_rng=rotation_rng,
            tower_floor_rng=tower_floor_rng,
        )

    def shuffle(
        self,
        selected_keys: Sequence[int] | None = None,
    ) -> SelectiveShuffleResult:
        if selected_keys is None:
            raise ValueError(
                "selective tower shuffle requires the keys pressed "
                "during the successful login"
            )
        pressed_keys = tuple(sorted({int(key) for key in selected_keys}))
        if not pressed_keys:
            raise ValueError("selected_keys must contain at least one key")
        if any(key < 0 or key >= self.k for key in pressed_keys):
            raise ValueError("selected_keys contains an out-of-range key")

        unpressed_keys = [
            key
            for key in range(self.k)
            if key not in pressed_keys
        ]
        if not unpressed_keys:
            raise ValueError(
                "selective tower shuffle requires at least one unpressed key"
            )
        extra_key = int(self.extra_key_rng.choice(unpressed_keys))
        rotation_keys = tuple(sorted((*pressed_keys, extra_key)))
        ring_size = len(rotation_keys)

        if ring_size == 2:
            if int(self.rotation_rng.integers(0, 2)) == 0:
                left_shift, right_shift = 1, 0
            else:
                left_shift, right_shift = 0, 1
        else:
            shifts = self.rotation_rng.permutation(
                np.arange(1, ring_size)
            )[:2]
            left_shift, right_shift = (int(shifts[0]), int(shifts[1]))

        left_columns = set(self.tower_shuffle.left_tower.tolist())
        before = self.keypad.copy()
        set_view = self.keypad.T.copy()
        ring_index = np.array(rotation_keys)
        for column in range(self.p):
            shift = (
                left_shift
                if column in left_columns
                else right_shift
            )
            if shift:
                set_view[column, ring_index] = np.roll(
                    set_view[column, ring_index],
                    shift,
                )
        self.keypad = set_view.T

        if left_shift == 0:
            fixed_columns = tuple(sorted(left_columns))
        elif right_shift == 0:
            fixed_columns = tuple(
                column
                for column in range(self.p)
                if column not in left_columns
            )
        else:
            fixed_columns = ()

        result = SelectiveShuffleResult(
            pressed_keys=pressed_keys,
            rotation_keys=rotation_keys,
            left_shift=left_shift,
            right_shift=right_shift,
            moved_icons=int(np.count_nonzero(before != self.keypad)),
            fixed_columns=fixed_columns,
        )
        self.tower_shuffle.shuffle(self.tower_floor_rng)
        return result


@dataclass
class RandomShuffleKeypad(BaseKeypad):
    keypad: np.ndarray
    k: int  # number of keys
    p: int  # properties per key
    rng: np.random.Generator = field(
        default_factory=np.random.default_rng,
        repr=False,
        compare=False,
    )

    @classmethod
    def new_keypad(
        cls,
        k: int,
        p: int,
        rng: np.random.Generator | None = None,
    ) -> Self:
        if rng is None:
            rng = np.random.default_rng()
        kp = cls._build_keypad(k, p, rng)
        return cls(keypad=kp, k=k, p=p, rng=rng)

    def shuffle(self):
        shuffled_matrix = np.array([
            self.rng.permutation(row)
            for row in self.keypad.T
        ])
        self.keypad = shuffled_matrix.T


@dataclass
class RandomSplitShuffleKeypad(BaseKeypad):
    keypad: np.ndarray
    k: int  # number of keys
    p: int  # properties per key
    rng: np.random.Generator = field(
        default_factory=np.random.default_rng,
        repr=False,
        compare=False,
    )

    @classmethod
    def new_keypad(
        cls,
        k: int,
        p: int,
        rng: np.random.Generator | None = None,
    ) -> Self:
        if rng is None:
            rng = np.random.default_rng()
        kp = cls._build_keypad(k, p, rng)
        return cls(keypad=kp, k=k, p=p, rng=rng)

    def shuffle(self):
        column_permutation = self.rng.permutation(self.p)
        column_subset = column_permutation[:self.p // 2]
        new_key_idxs = self.rng.permutation(self.k)
        shuffled_sets = self.keypad.copy()
        shuffled_sets[:, column_subset] = shuffled_sets[
            new_key_idxs, :
        ][:, column_subset]
        self.keypad = shuffled_sets


@dataclass
class SlidingSplitShuffleKeypad(BaseKeypad):
    keypad: np.ndarray
    k: int  # number of keys
    p: int  # properties per key
    rng: np.random.Generator = field(
        default_factory=np.random.default_rng,
        repr=False,
        compare=False,
    )

    @classmethod
    def new_keypad(
        cls,
        k: int,
        p: int,
        rng: np.random.Generator | None = None,
    ) -> Self:
        if rng is None:
            rng = np.random.default_rng()
        kp = cls._build_keypad(k, p, rng)
        return cls(keypad=kp, k=k, p=p, rng=rng)

    def shuffle(self):
        selected_positions = self.rng.permutation(self.p)
        column_subset = selected_positions[:self.p // 2]
        shift = self.rng.integers(1, self.k)
        new_key_idxs = np.roll(np.arange(self.k), shift)
        shuffled_sets = self.keypad.copy()
        shuffled_sets[:, column_subset] = shuffled_sets[
            new_key_idxs, :
        ][:, column_subset]
        self.keypad = shuffled_sets
