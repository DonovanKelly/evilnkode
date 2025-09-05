from src.evilkode import Evilkode
from dataclasses import dataclass
from statistics import mean, variance
from pathlib import Path

from src.utils import ShuffleTypes, observations, passcode_generator


@dataclass
class Benchmark:
    iterations_to_break: list[int]
    iterations_to_replay: list[int]


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
    # file_name_break = f"{shuffle_type.name.lower()}-{number_of_keys}-{properties_per_key}-{passcode_len}-{max_tries_before_lockout}-{complexity}-{disparity}-{run_count}.txt"
    # full_path_iter_break = Path(file_path) / "iterations_to_break" /file_name_break
    # if not overwrite and full_path_iter_break.exists():
    #     print(f"file exists {file_path}")
    #     with open(full_path_iter_break, "r") as fp:
    #         iterations_to_break = fp.readline()
    #         iterations_to_break = iterations_to_break.split(',')
    #         iterations_to_break = [int(i) for i in iterations_to_break]
    #         return  Benchmark(
    #             mean=mean(iterations_to_break),
    #             variance=variance(iterations_to_break),
    #             iterations_to_break=iterations_to_break
    #         )
    iterations_to_break = []
    iterations_to_replay = []
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
        iterations_to_break.append(evilout.iterations_to_break)
        iterations_to_replay.append(evilout.iterations_to_replay)

    # full_path_iter_break.parent.mkdir(parents=True, exist_ok=True)
    # with open(full_path_iter_break, "w") as fp:
    #    fp.write(",".join([str(i) for i in iterations_to_break])),

    return Benchmark(
        iterations_to_break=iterations_to_break,
        iterations_to_replay=iterations_to_replay
    )


# def full_shuffle_benchmark(
#         number_of_keys: int,
#         properties_per_key: int,
#         passcode_len: int,
#         max_tries_before_lockout: int,
#         run_count: int,
#         complexity: int,
#         disparity: int,
# ) -> Benchmark:
#     runs = []
#     for _ in range(run_count):
#         passcode = passcode_generator(number_of_keys, properties_per_key, passcode_len, complexity, disparity)
#         evilkode = Evilkode(
#             observations=observations(
#                 target_passcode=passcode,
#                 number_of_keys=number_of_keys,
#                 properties_per_key=properties_per_key,
#                 min_complexity=complexity,
#                 min_disparity=disparity,
#                 shuffle_type=ShuffleTypes.FULL_SHUFFLE,
#             ),
#             number_of_keys=number_of_keys,
#             properties_per_key=properties_per_key,
#             passcode_len=passcode_len,
#             max_tries_before_lockout=max_tries_before_lockout,
#         )
#         evilout = evilkode.run()
#         runs.append(evilout.iterations_to_break)
#
#     return Benchmark(
#         mean=mean(runs),
#         variance=variance(runs),
#         iterations_to_break=runs
#     )
