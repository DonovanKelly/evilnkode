import random
import pytest

from src.evilnkode import EvilNKode, Observation
from src.keypad.keypad import (
    RandomShuffleKeypad,
    SlidingTowerShuffleKeypad,
)
from src.utils import observations


@pytest.fixture
def passcode(number_of_keys, properties_per_key, passcode_len):
    return [random.randint(0, number_of_keys * properties_per_key - 1) for _ in range(passcode_len)]


@pytest.mark.parametrize(
    "number_of_keys, properties_per_key, passcode_len",
    [
        (5, 4, 4),  # Test case 1
        (10, 5, 6),  # Test case 2
        (8, 4, 5),  # Test case 3
    ]
)
def test_evilkode(number_of_keys, properties_per_key, passcode_len, passcode):
    keypad = RandomShuffleKeypad.new_keypad(number_of_keys, properties_per_key)
    obs = observations(passcode, keypad)
    evilkode = EvilNKode(
        observations=obs,
        number_of_keys=number_of_keys,
        properties_per_key=properties_per_key,
        passcode_len=passcode_len,
    )
    evilout = evilkode.run()
    assert evilout.iterations_to_break > 1


def test_eight_icons_per_key_breaks_after_four_observations():
    keypad = SlidingTowerShuffleKeypad.new_keypad(k=6, p=8)
    passcode = [0, 9, 18, 27]
    evilkode = EvilNKode(
        observations=observations(passcode, keypad, number_of_observations=10),
        number_of_keys=6,
        properties_per_key=8,
        passcode_len=4,
    )

    evilout = evilkode.run()

    assert evilout.iterations_to_break == 4
    assert evilout.iterations_to_replay == 4


def test_break_counts_the_observation_that_crosses_the_threshold():
    observation_sequence = iter([
        Observation(
            keypad=[[0, 1], [2, 3]],
            key_selection=[0],
        ),
        Observation(
            keypad=[[0, 2], [1, 3]],
            key_selection=[0],
        ),
    ])
    evilkode = EvilNKode(
        observations=observation_sequence,
        number_of_keys=2,
        properties_per_key=2,
        passcode_len=1,
        max_tries_before_lockout=1,
    )

    evilout = evilkode.run()

    assert evilout.iterations_to_break == 2
    assert evilout.iterations_to_replay == 2
