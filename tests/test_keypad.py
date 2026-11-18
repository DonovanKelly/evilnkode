import pytest
import numpy as np
from src.keypad.keypad import (
    RandomSplitShuffleKeypad,
    RandomShuffleKeypad,
    SelectiveTowerShuffleKeypad,
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


def _selective_keypad(seed):
    return SelectiveTowerShuffleKeypad.new_keypad(
        k=6,
        p=8,
        rng=np.random.default_rng(seed),
        tower_init_rng=np.random.default_rng(seed + 1),
        extra_key_rng=np.random.default_rng(seed + 2),
        rotation_rng=np.random.default_rng(seed + 3),
        tower_floor_rng=np.random.default_rng(seed + 4),
    )


def _key_by_icon(keypad):
    return {
        int(icon): key
        for key, row in enumerate(keypad)
        for icon in row
    }


@pytest.mark.parametrize(
    "pressed_keys, expected_ring_size, expected_moved_icons",
    [
        ([0, 0, 0], 2, 8),
        ([0, 2, 2], 3, 24),
        ([0, 2, 4], 4, 32),
    ],
)
def test_selective_tower_shuffle_touches_pressed_keys_plus_one(
    pressed_keys,
    expected_ring_size,
    expected_moved_icons,
):
    keypad = _selective_keypad(100 + expected_ring_size)
    before = keypad.keypad.copy()
    candidate_icons = before[pressed_keys[0]].copy()

    result = keypad.shuffle(pressed_keys)

    assert result.pressed_keys == tuple(sorted(set(pressed_keys)))
    assert len(result.rotation_keys) == expected_ring_size
    assert set(result.pressed_keys) < set(result.rotation_keys)
    assert result.moved_icons == expected_moved_icons
    assert sorted(keypad.keypad.flatten()) == list(range(48))
    assert all(
        np.array_equal(keypad.keypad[key], before[key])
        for key in set(range(6)) - set(result.rotation_keys)
    )
    assert len({
        _key_by_icon(keypad.keypad)[int(icon)]
        for icon in candidate_icons
    }) == 2

    if expected_ring_size == 2:
        assert {result.left_shift, result.right_shift} == {0, 1}
        assert len(result.fixed_columns) == 4
    else:
        assert result.left_shift != 0
        assert result.right_shift != 0
        assert result.left_shift != result.right_shift
        assert result.fixed_columns == ()

    left = set(keypad.tower_shuffle.left_tower.tolist())
    right = set(keypad.tower_shuffle.right_tower.tolist())
    assert left.isdisjoint(right)
    assert left | right == set(range(8))
    assert len(left) == len(right) == 4


def test_selective_tower_shuffle_is_seeded_and_has_independent_state():
    first = _selective_keypad(700)
    second = _selective_keypad(700)
    selections = ([0, 0, 0], [1, 3, 3], [0, 2, 5])

    for selected_keys in selections:
        assert np.array_equal(first.keypad, second.keypad)
        assert first.tower_shuffle is not second.tower_shuffle
        assert first.tower_shuffle.left_tower is not (
            second.tower_shuffle.left_tower
        )
        assert first.shuffle(selected_keys) == second.shuffle(selected_keys)
        assert np.array_equal(first.keypad, second.keypad)
        assert (
            first.tower_shuffle.left_tower.tolist()
            == second.tower_shuffle.left_tower.tolist()
        )


def test_selective_tower_shuffle_rejects_invalid_selected_keys():
    keypad = _selective_keypad(800)

    with pytest.raises(ValueError, match="requires the keys pressed"):
        keypad.shuffle()
    with pytest.raises(ValueError, match="at least one key"):
        keypad.shuffle([])
    with pytest.raises(ValueError, match="out-of-range"):
        keypad.shuffle([6])
    with pytest.raises(ValueError, match="unpressed key"):
        keypad.shuffle(range(6))


@pytest.mark.parametrize(
    "keypad_type",
    [
        RandomShuffleKeypad,
        RandomSplitShuffleKeypad,
        SlidingTowerShuffleKeypad,
        SlidingSplitShuffleKeypad,
    ],
)
def test_seeded_keypads_are_reproducible(keypad_type):
    first = keypad_type.new_keypad(
        k=6,
        p=9,
        rng=np.random.default_rng(123),
    )
    second = keypad_type.new_keypad(
        k=6,
        p=9,
        rng=np.random.default_rng(123),
    )
    expected_icons = list(range(54))

    for _ in range(5):
        assert np.array_equal(first.keypad, second.keypad)
        assert sorted(first.keypad.flatten()) == expected_icons
        first.shuffle()
        second.shuffle()
    assert sorted(first.keypad.flatten()) == expected_icons


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
