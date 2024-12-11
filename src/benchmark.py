from src.evilkode import Observation, Evilkode
from src.keypad import Keypad
import random
from dataclasses import dataclass
from statistics import mean, variance
from enum import Enum

@dataclass
class Benchmark:
    mean: int
    variance: int
    runs: list[int]

class ShuffleTypes(Enum):
    FULL_SHUFFLE = "FULL_SHUFFLE"
    SPLIT_SHUFFLE = "SPLIT_SHUFFLE"

def observations(number_of_keys, properties_per_key, passcode_len, shuffle_type: ShuffleTypes = ShuffleTypes.SPLIT_SHUFFLE):
    k = number_of_keys
    p = properties_per_key
    n = passcode_len
    nkode = [random.randint(0, k*p-1) for _ in range(n)]
    keypad = Keypad.new_keypad(k, p)

    def obs_gen():
        for _ in range(100):  # finite number of yields
            yield Observation(
                keypad=keypad.keypad.copy(),
                key_selection=keypad.key_entry(target_passcode=nkode)
            )
            match shuffle_type:
                case ShuffleTypes.FULL_SHUFFLE:
                    keypad.full_shuffle()
                case ShuffleTypes.SPLIT_SHUFFLE:
                    keypad.split_shuffle()
                case _:
                    raise Exception(f"no shuffle type {shuffle_type}")

    return obs_gen()

def split_shuffle_benchmark(
        number_of_keys: int,
        properties_per_key: int,
        passcode_len: int,
        max_tries_before_lockout: int,
        run_count: int,
) -> Benchmark:
    runs = []
    for _ in range(run_count):
        evilkode = Evilkode(
            observations=observations(number_of_keys, properties_per_key, passcode_len),
            number_of_keys=number_of_keys,
            properties_per_key=properties_per_key,
            passcode_len=passcode_len,
            max_tries_before_lockout=max_tries_before_lockout
        )
        evilout = evilkode.run()
        runs.append(evilout.iterations)

    return Benchmark(
        mean=mean(runs),
        variance=variance(runs),
        runs=runs
    )


def full_shuffle_benchmark(
        number_of_keys: int,
        properties_per_key: int,
        passcode_len: int,
        max_tries_before_lockout: int,
        run_count: int,
) -> Benchmark:
    runs = []
    for _ in range(run_count):
        evilkode = Evilkode(
            observations=observations(number_of_keys, properties_per_key, passcode_len, shuffle_type=ShuffleTypes.FULL_SHUFFLE),
            number_of_keys=number_of_keys,
            properties_per_key=properties_per_key,
            passcode_len=passcode_len,
            max_tries_before_lockout=max_tries_before_lockout
        )
        evilout = evilkode.run()
        runs.append(evilout.iterations)

    return Benchmark(
        mean=mean(runs),
        variance=variance(runs),
        runs=runs
    )
