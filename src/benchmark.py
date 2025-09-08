from src.evilnkode import EvilNKode
from dataclasses import dataclass

from src.utils import observations, passcode_generator
from src.keypad.keypad import BaseKeypad
from pathlib import Path


@dataclass
class Benchmark:
    iterations_to_break: list[int]
    iterations_to_replay: list[int]


def benchmark(
        number_of_keys: int,
        properties_per_key: int,
        passcode_len: int,
        max_tries_before_lockout: int,
        run_count: int,
        complexity: int,
        disparity: int,
        keypad: BaseKeypad,
        file_path: str = '../output',
        overwrite: bool = False
) -> Benchmark:
    shuffle_type = str(type(keypad))
    file_name_break = f"{shuffle_type.lower()}-{number_of_keys}-{properties_per_key}-{passcode_len}-{max_tries_before_lockout}-{complexity}-{disparity}-{run_count}.txt"
    full_path_iter_break = Path(file_path) / "iterations_to_break" / file_name_break
    file_name_replay = f"{shuffle_type.lower()}-{number_of_keys}-{properties_per_key}-{passcode_len}-{max_tries_before_lockout}-{complexity}-{disparity}-{run_count}.txt"
    full_path_iter_replay = Path(file_path) / "iterations_to_replay" / file_name_replay
    iterations_to_break = []
    iterations_to_replay = []
    if not overwrite and full_path_iter_break.exists() and full_path_iter_replay.exists():
        print(f"file exists {file_path}")
        with open(full_path_iter_break, "r") as fp:
            iterations_to_break = fp.readline()
            iterations_to_break = iterations_to_break.split(',')
            iterations_to_break = [int(i) for i in iterations_to_break]
        with open(full_path_iter_replay, "r") as fp:
            iterations_to_replay = fp.readline()
            iterations_to_replay = iterations_to_replay.split(',')
            iterations_to_replay = [int(i) for i in iterations_to_replay]
        return Benchmark(
            iterations_to_break=iterations_to_break,
            iterations_to_replay=iterations_to_replay
        )
    for _ in range(run_count):
        passcode = passcode_generator(number_of_keys, properties_per_key, passcode_len, complexity, disparity)
        evilnkode = EvilNKode(
            observations=observations(
                target_passcode=passcode,
                keypad=keypad,
            ),
            number_of_keys=number_of_keys,
            properties_per_key=properties_per_key,
            passcode_len=passcode_len,
            max_tries_before_lockout=max_tries_before_lockout,
        )
        evilout = evilnkode.run()
        iterations_to_break.append(evilout.iterations_to_break)
        iterations_to_replay.append(evilout.iterations_to_replay)

    if not file_path == "":
        full_path_iter_break.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path_iter_break, "w") as fp:
            fp.write(",".join([str(i) for i in iterations_to_break])),

    return Benchmark(
        iterations_to_break=iterations_to_break,
        iterations_to_replay=iterations_to_replay
    )
