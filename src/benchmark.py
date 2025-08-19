from src.evilkode import Evilkode
from dataclasses import dataclass
from statistics import mean, variance
from pathlib import Path

from src.utils import ShuffleTypes, observations, passcode_generator


@dataclass
class Benchmark:
    mean: int
    variance: int
    runs: list[int]


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
        passcode = passcode_generator(number_of_keys, properties_per_key, passcode_len, complexity, disparity)
        evilkode = Evilkode(
            observations=observations(
                target_passcode=passcode,
                number_of_keys=number_of_keys,
                properties_per_key=properties_per_key,
                min_complexity=complexity,
                min_disparity=disparity,
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
        passcode = passcode_generator(number_of_keys, properties_per_key, passcode_len, complexity, disparity)
        evilkode = Evilkode(
            observations=observations(
                target_passcode=passcode,
                number_of_keys=number_of_keys,
                properties_per_key=properties_per_key,
                min_complexity=complexity,
                min_disparity=disparity,
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
