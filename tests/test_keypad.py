import pytest
import numpy as np
from src.keypad.keypad import (
    RandomSplitShuffleKeypad,
    RandomShuffleKeypad,
    SlidingSplitShuffleKeypad,
    SlidingTowerShuffleKeypad,
)


def test_key_entry():
    keypad = RandomShuffleKeypad(
        keypad=np.array([
            [8, 9, 10, 11],
            [0, 5, 2, 3],
            [4, 1, 6, 7]
        ]), k=3, p=4)
    assert keypad.key_entry([8, 5, 6, 11]) == [0, 1, 2, 0]


def test_sliding_tower_shuffle_matches_nkode_rotations():
    keypad = SlidingTowerShuffleKeypad.new_keypad(k=6, p=8)
    before = keypad.keypad.copy()
    left_positions = set(keypad.tower_shuffle.left_tower.tolist())

    keypad.shuffle()

    shifts_by_tower = {True: set(), False: set()}
    for column in range(keypad.p):
        shifts = [
            shift
            for shift in range(keypad.k)
            if np.array_equal(
                np.roll(before[:, column], shift),
                keypad.keypad[:, column],
            )
        ]
        assert len(shifts) == 1
        shifts_by_tower[column in left_positions].add(shifts[0])

    assert len(shifts_by_tower[True]) == 1
    assert len(shifts_by_tower[False]) == 1
    left_shift = shifts_by_tower[True].pop()
    right_shift = shifts_by_tower[False].pop()
    assert left_shift != 0
    assert right_shift != 0
    assert left_shift != right_shift
    assert sorted(keypad.keypad.flatten()) == sorted(before.flatten())


@pytest.mark.parametrize(
    "keypad_type, number_of_keys, properties_per_key",
    [
        (RandomShuffleKeypad, 3, 4),
        (RandomSplitShuffleKeypad, 3, 4),
        (SlidingTowerShuffleKeypad, 3, 4),
        (SlidingSplitShuffleKeypad, 3, 4),
    ]
)
def test_keypad_shuffle(keypad_type, number_of_keys, properties_per_key):
    keypad = keypad_type.new_keypad(number_of_keys, properties_per_key)
    print(keypad.keypad)
    keypad.shuffle()
    print(keypad.keypad)
