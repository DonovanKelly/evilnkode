from src.evilkode import Observation, Evilkode
from src.keypad import Keypad
import random
from dataclasses import dataclass
from statistics import mean, variance
from enum import Enum
from pathlib import Path

@dataclass
class Benchmark:
    mean: int
    variance: int
    runs: list[int]

class ShuffleTypes(Enum):
    FULL_SHUFFLE = "FULL_SHUFFLE"
    SPLIT_SHUFFLE = "SPLIT_SHUFFLE"

def observations(number_of_keys, properties_per_key, passcode_len, complexity: int, disparity: int, shuffle_type: ShuffleTypes):
    k = number_of_keys
    p = properties_per_key
    n = passcode_len
    passcode =  passcode_generator(k, p, n, complexity, disparity)
    keypad = Keypad.new_keypad(k, p)

    def obs_gen():
        for _ in range(100):  # finite number of yields
            yield Observation(
                keypad=keypad.keypad.copy(),
                key_selection=keypad.key_entry(target_passcode=passcode)
            )
            match shuffle_type:
                case ShuffleTypes.FULL_SHUFFLE:
                    keypad.full_shuffle()
                case ShuffleTypes.SPLIT_SHUFFLE:
                    keypad.split_shuffle()
                case _:
                    raise Exception(f"no shuffle type {shuffle_type}")

    return obs_gen()

def passcode_generator(k: int, p: int, n: int, c: int, d: int) -> list[int]:
    assert n >= c
    assert p*k >= c

    assert n >= d
    assert p >= d
    passcode_prop = []
    passcode_set = []
    valid_choices = {i for i in range(k*p)}
    repeat_set = n-d
    repeat_prop = n-c
    prop_added = set()
    set_added = set()

    for _ in range(n):
        prop = random.choice(list(valid_choices))
        prop_set = prop//p
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


def shuffle_benchmark(
        number_of_keys: int,
        properties_per_key: int,
        passcode_len: int,
        max_tries_before_lockout: int,
        run_count: int,
        complexity: int,
        disparity: int,
        shuffle_type: ShuffleTypes,
        file_path: str = '../output',
        overwrite: bool = False
) -> Benchmark:
    file_name = f"{shuffle_type.name.lower()}-{number_of_keys}-{properties_per_key}-{passcode_len}-{max_tries_before_lockout}-{complexity}-{disparity}-{run_count}.txt"
    full_path = Path(file_path) / file_name
    if not overwrite and full_path.exists():
        print(f"file exists {file_path}")
        with open(full_path, "r") as fp:
            runs = fp.readline()
            runs = runs.split(',')
            runs = [int(i) for i in runs]
            return  Benchmark(
                mean=mean(runs),
                variance=variance(runs),
                runs=runs
            )
    runs = []
    for _ in range(run_count):
        evilkode = Evilkode(
            observations=observations(
                number_of_keys=number_of_keys,
                properties_per_key=properties_per_key,
                passcode_len=passcode_len,
                complexity=complexity,
                disparity=disparity,
                shuffle_type=shuffle_type,
            ),
            number_of_keys=number_of_keys,
            properties_per_key=properties_per_key,
            passcode_len=passcode_len,
            max_tries_before_lockout=max_tries_before_lockout,
        )
        evilout = evilkode.run()
        runs.append(evilout.iterations)

    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w") as fp:
       fp.write(",".join([str(i) for i in runs])),

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
        complexity: int,
        disparity: int,
) -> Benchmark:
    runs = []
    for _ in range(run_count):
        evilkode = Evilkode(
            observations=observations(
                number_of_keys=number_of_keys,
                properties_per_key=properties_per_key,
                passcode_len=passcode_len,
                complexity=complexity,
                disparity=disparity,
                shuffle_type=ShuffleTypes.FULL_SHUFFLE,
            ),
            number_of_keys=number_of_keys,
            properties_per_key=properties_per_key,
            passcode_len=passcode_len,
            max_tries_before_lockout=max_tries_before_lockout,
        )
        evilout = evilkode.run()
        runs.append(evilout.iterations)

    return Benchmark(
        mean=mean(runs),
        variance=variance(runs),
        runs=runs
    )
