import argparse
from pathlib import Path

from src.challenge_schedule import CHALLENGE_SCHEDULES
from src.challenge_subset import (
    SELECTIVE_TOWER,
    ChallengeSubsetConfig,
    run_challenge_subset_benchmark,
    write_challenge_subset_artifacts,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare uniform and alternating 3-of-6 challenges with the "
            "selective tower shuffle"
        )
    )
    parser.add_argument("--number-of-keys", type=int, default=6)
    parser.add_argument("--icons-per-key", type=int, default=8)
    parser.add_argument("--secret-length", type=int, default=6)
    parser.add_argument("--challenge-length", type=int, default=3)
    parser.add_argument("--max-tries", type=int, default=3)
    parser.add_argument("--run-count", type=int, default=10_000)
    parser.add_argument("--max-observations", type=int, default=30)
    parser.add_argument("--curve-observations", type=int, default=15)
    parser.add_argument("--seed", type=int, default=20_260_725)
    parser.add_argument(
        "--challenge-schedule",
        choices=("all", *CHALLENGE_SCHEDULES),
        default="all",
        help="run both challenge schedules or select one",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./output/challenge-subset"),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace artifacts for an identical configuration",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    challenge_schedules = (
        CHALLENGE_SCHEDULES
        if args.challenge_schedule == "all"
        else (args.challenge_schedule,)
    )
    config = ChallengeSubsetConfig(
        number_of_keys=args.number_of_keys,
        icons_per_key=args.icons_per_key,
        secret_length=args.secret_length,
        challenge_length=args.challenge_length,
        max_tries=args.max_tries,
        run_count=args.run_count,
        max_observations=args.max_observations,
        curve_observations=args.curve_observations,
        seed=args.seed,
        challenge_schedules=challenge_schedules,
    )

    progress_interval = max(1, config.run_count // 10)

    def show_progress(completed: int, total: int) -> None:
        if completed % progress_interval == 0 or completed == total:
            print(f"Completed {completed:,}/{total:,} trial scenarios")

    result = run_challenge_subset_benchmark(
        config=config,
        progress=show_progress,
    )
    output_dir = write_challenge_subset_artifacts(
        result=result,
        output_root=args.output_dir,
        overwrite=args.overwrite,
    )

    summary = result.summary()
    for schedule in result.challenge_schedules:
        schedule_summary = summary["results"][schedule][SELECTIVE_TOWER]
        break_mean = schedule_summary["break_observations"]["mean"]
        replay_mean = schedule_summary[
            "guaranteed_replay_observations"
        ]["mean"]
        print(
            f"{schedule}: crack={break_mean:.2f}, "
            f"guaranteed replay={replay_mean:.2f} observations"
        )
    print(f"Artifacts: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
