import argparse
from pathlib import Path

from src.challenge_subset import (
    ChallengeSubsetConfig,
    run_challenge_subset_benchmark,
    write_challenge_subset_artifacts,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare random and tower shuffling for challenge-subset nKode"
        )
    )
    parser.add_argument("--number-of-keys", type=int, default=6)
    parser.add_argument("--icons-per-key", type=int, default=9)
    parser.add_argument("--secret-length", type=int, default=6)
    parser.add_argument("--challenge-length", type=int, default=3)
    parser.add_argument("--max-tries", type=int, default=3)
    parser.add_argument("--run-count", type=int, default=10_000)
    parser.add_argument("--max-observations", type=int, default=30)
    parser.add_argument("--curve-observations", type=int, default=15)
    parser.add_argument("--seed", type=int, default=20_260_725)
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
    )

    progress_interval = max(1, config.run_count // 10)

    def show_progress(completed: int, total: int) -> None:
        if completed % progress_interval == 0 or completed == total:
            print(f"Completed {completed:,}/{total:,} paired trials")

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
    for shuffle in result.shuffles:
        shuffle_summary = summary["shuffle_results"][shuffle]
        break_mean = shuffle_summary["break_observations"]["mean"]
        replay_mean = shuffle_summary[
            "guaranteed_replay_observations"
        ]["mean"]
        print(
            f"{shuffle.title()}: crack={break_mean:.2f}, "
            f"guaranteed replay={replay_mean:.2f} observations"
        )
    print(f"Artifacts: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
