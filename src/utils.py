import random
from math import factorial, comb
import numpy as np

from src.evilnkode import Observation
from src.keypad.keypad import BaseKeypad
from typing import Iterator


def total_valid_nkode_states(k: int, p: int) -> int:
    return factorial(k) ** (p - 1)


def total_shuffle_states(k: int, p: int) -> int:
    return comb((p - 1), (p - 1) // 2) * factorial(k)


def observations(
    target_passcode: list[int],
    keypad: BaseKeypad,
    number_of_observations: int = 100,
    challenge_length: int | None = None,
    rng: np.random.Generator | None = None,
) -> Iterator[Observation]:
    if (
        challenge_length is not None
        and not 1 <= challenge_length <= len(target_passcode)
    ):
        raise ValueError("challenge_length must be between 1 and the secret length")
    if rng is None:
        rng = np.random.default_rng()

    def obs():
        for _ in range(number_of_observations):
            if challenge_length is None:
                challenge_positions = None
                challenged_passcode = target_passcode
            else:
                challenge_positions = tuple(sorted(
                    int(position)
                    for position in rng.choice(
                        len(target_passcode),
                        size=challenge_length,
                        replace=False,
                    )
                ))
                challenged_passcode = [
                    target_passcode[position]
                    for position in challenge_positions
                ]
            yield Observation(
                keypad=keypad.keypad_mat(),
                key_selection=keypad.key_entry(
                    target_passcode=challenged_passcode,
                ),
                challenge_positions=challenge_positions,
            )
            keypad.shuffle()

    return obs()


def passcode_generator(k: int, p: int, n: int, c: int, d: int) -> list[int]:
    assert n >= c
    assert p * k >= c

    assert n >= d
    assert p >= d
    passcode_prop = []
    passcode_set = []
    valid_choices = {i for i in range(k * p)}
    repeat_set = n - d
    repeat_prop = n - c
    prop_added = set()
    set_added = set()

    for _ in range(n):
        prop = random.choice(list(valid_choices))
        prop_set = prop // p
        passcode_prop.append(prop)
        passcode_set.append(prop_set)

        if prop in prop_added:
            repeat_prop -= 1
        if prop_set in set_added:
            repeat_set -= 1

        prop_added.add(prop)
        set_added.add(prop_set)

        if repeat_prop <= 0:
            valid_choices -= prop_added

        if repeat_set <= 0:
            for el in valid_choices.copy():
                if el // p in set_added:
                    valid_choices.remove(el)

    return passcode_prop
