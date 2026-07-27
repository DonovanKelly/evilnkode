import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, median
from typing import Callable

import numpy as np

from src.challenge_schedule import (
    ALTERNATING_HALVES,
    CHALLENGE_SCHEDULES,
    UNIFORM,
    ChallengeScheduler,
    new_challenge_scheduler,
    random_challenge,
)
from src.challenge_protocol import ChallengeSubsetProtocol
from src.evilnkode import AttackState, Observation
from src.keypad.keypad import (
    SelectiveShuffleResult,
    SelectiveTowerShuffleKeypad,
)


ProgressCallback = Callable[[int, int], None]
SELECTIVE_TOWER = "selective-tower"


@dataclass(frozen=True)
class ChallengeSubsetConfig:
    number_of_keys: int = 6
    icons_per_key: int = 8
    secret_length: int = 6
    challenge_length: int = 3
    max_tries: int = 3
    run_count: int = 10_000
    max_observations: int = 30
    curve_observations: int = 15
    seed: int = 20_260_725
    challenge_schedules: tuple[str, ...] = CHALLENGE_SCHEDULES

    def __post_init__(self) -> None:
        if self.number_of_keys < 2:
            raise ValueError("number_of_keys must be at least 2")
        if self.icons_per_key < 3:
            raise ValueError("icons_per_key must be at least 3")
        if not 1 <= self.challenge_length <= self.secret_length:
            raise ValueError(
                "challenge_length must be between 1 and secret_length"
            )
        if self.challenge_length >= self.number_of_keys:
            raise ValueError(
                "number_of_keys must exceed challenge_length so an "
                "unpressed key is always available"
            )
        if self.secret_length > self.total_icons:
            raise ValueError("secret_length cannot exceed the icon count")
        if self.max_tries < 1:
            raise ValueError("max_tries must be positive")
        if self.run_count < 1:
            raise ValueError("run_count must be positive")
        if self.max_observations < 1:
            raise ValueError("max_observations must be positive")
        if not 0 <= self.curve_observations <= self.max_observations:
            raise ValueError(
                "curve_observations must be between 0 and max_observations"
            )
        if not self.challenge_schedules:
            raise ValueError("at least one challenge schedule is required")
        if len(set(self.challenge_schedules)) != len(
            self.challenge_schedules
        ):
            raise ValueError("challenge schedules must be unique")
        unknown_schedules = set(self.challenge_schedules) - set(
            CHALLENGE_SCHEDULES
        )
        if unknown_schedules:
            raise ValueError(
                f"unknown challenge schedules: {sorted(unknown_schedules)}"
            )
        if (
            ALTERNATING_HALVES in self.challenge_schedules
            and self.secret_length != self.challenge_length * 2
        ):
            raise ValueError(
                "alternating-halves requires the secret length to be exactly "
                "twice the challenge length"
            )

    @property
    def total_icons(self) -> int:
        return self.number_of_keys * self.icons_per_key

    @property
    def run_name(self) -> str:
        if self.challenge_schedules == CHALLENGE_SCHEDULES:
            schedule_name = "all"
        else:
            schedule_name = "_".join(self.challenge_schedules)
        return (
            f"{self.challenge_length}of{self.secret_length}"
            f"-keys{self.number_of_keys}"
            f"-icons{self.icons_per_key}"
            f"-shuffle-{SELECTIVE_TOWER}"
            f"-schedules-{schedule_name}"
            f"-tries{self.max_tries}"
            f"-runs{self.run_count}"
            f"-seed{self.seed}"
        )


@dataclass(frozen=True)
class ChallengeSubsetTrial:
    trial: int
    challenge_schedule: str
    keypad_shuffle: str
    observations_to_break: int
    observations_to_guaranteed_replay: int
    replay_success_curve: tuple[float, ...]
    position_coverage_curve: tuple[int, ...]
    challenges: tuple[tuple[int, ...], ...]
    challenge_overlaps: tuple[int | None, ...]
    shuffle_results: tuple[SelectiveShuffleResult, ...]

    @property
    def mean_rotation_keys(self) -> float:
        return mean(
            len(result.rotation_keys)
            for result in self.shuffle_results
        )

    @property
    def mean_moved_icons(self) -> float:
        return mean(result.moved_icons for result in self.shuffle_results)

    @property
    def mean_fixed_columns(self) -> float:
        return mean(
            len(result.fixed_columns)
            for result in self.shuffle_results
        )

    @property
    def max_fixed_column_streak(self) -> int:
        active_streaks: dict[int, int] = {}
        maximum = 0
        for result in self.shuffle_results:
            active_streaks = {
                column: active_streaks.get(column, 0) + 1
                for column in result.fixed_columns
            }
            if active_streaks:
                maximum = max(maximum, max(active_streaks.values()))
        return maximum


@dataclass(frozen=True)
class ChallengeSubsetResult:
    config: ChallengeSubsetConfig
    trials: tuple[ChallengeSubsetTrial, ...]

    def trials_for(
        self,
        challenge_schedule: str,
        keypad_shuffle: str = SELECTIVE_TOWER,
    ) -> list[ChallengeSubsetTrial]:
        return [
            trial
            for trial in self.trials
            if (
                trial.challenge_schedule == challenge_schedule
                and trial.keypad_shuffle == keypad_shuffle
            )
        ]

    @property
    def challenge_schedules(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                trial.challenge_schedule
                for trial in self.trials
            )
        )

    @property
    def keypad_shuffles(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(trial.keypad_shuffle for trial in self.trials)
        )

    def summary(self) -> dict:
        schedule_results = {}
        for schedule in self.challenge_schedules:
            trials = self.trials_for(schedule)
            overlaps = [
                overlap
                for trial in trials
                for overlap in trial.challenge_overlaps
                if overlap is not None
            ]
            schedule_results[schedule] = {
                SELECTIVE_TOWER: {
                    "break_observations": _summary_statistics([
                        trial.observations_to_break
                        for trial in trials
                    ]),
                    "guaranteed_replay_observations": _summary_statistics([
                        trial.observations_to_guaranteed_replay
                        for trial in trials
                    ]),
                    "next_login_success": {
                        str(observation_count): mean(
                            trial.replay_success_curve[observation_count]
                            for trial in trials
                        )
                        for observation_count in range(
                            self.config.curve_observations + 1
                        )
                    },
                    "position_coverage": {
                        str(observation_count): mean(
                            trial.position_coverage_curve[observation_count]
                            for trial in trials
                        )
                        for observation_count in range(
                            self.config.curve_observations + 1
                        )
                    },
                    "mean_consecutive_overlap": (
                        mean(overlaps) if overlaps else 0.0
                    ),
                    "mean_rotation_keys": mean(
                        trial.mean_rotation_keys
                        for trial in trials
                    ),
                    "mean_moved_icons": mean(
                        trial.mean_moved_icons
                        for trial in trials
                    ),
                    "mean_fixed_columns": mean(
                        trial.mean_fixed_columns
                        for trial in trials
                    ),
                    "mean_max_fixed_column_streak": mean(
                        trial.max_fixed_column_streak
                        for trial in trials
                    ),
                }
            }

        paired_deltas = {}
        if (
            UNIFORM in self.challenge_schedules
            and ALTERNATING_HALVES in self.challenge_schedules
        ):
            uniform_trials = {
                trial.trial: trial
                for trial in self.trials_for(UNIFORM)
            }
            alternating_trials = {
                trial.trial: trial
                for trial in self.trials_for(ALTERNATING_HALVES)
            }
            paired_trial_ids = sorted(
                set(uniform_trials) & set(alternating_trials)
            )
            paired_deltas[
                f"{ALTERNATING_HALVES}_minus_{UNIFORM}"
            ] = {
                SELECTIVE_TOWER: {
                    "break_observations": _summary_statistics([
                        alternating_trials[
                            trial_id
                        ].observations_to_break
                        - uniform_trials[
                            trial_id
                        ].observations_to_break
                        for trial_id in paired_trial_ids
                    ]),
                    "guaranteed_replay_observations": _summary_statistics([
                        alternating_trials[
                            trial_id
                        ].observations_to_guaranteed_replay
                        - uniform_trials[
                            trial_id
                        ].observations_to_guaranteed_replay
                        for trial_id in paired_trial_ids
                    ]),
                }
            }

        return {
            "config": asdict(self.config),
            "results": schedule_results,
            "paired_deltas": paired_deltas,
        }


def _nearest_rank(values: list[int], probability: float) -> int:
    ordered = sorted(values)
    return ordered[math.ceil(probability * len(ordered)) - 1]


def _summary_statistics(values: list[int]) -> dict[str, float | int]:
    if not values:
        raise ValueError("summary statistics require at least one value")
    return {
        "mean": mean(values),
        "median": median(values),
        "p90": _nearest_rank(values, 0.90),
        "p95": _nearest_rank(values, 0.95),
        "minimum": min(values),
        "maximum": max(values),
    }


def _random_challenge(
    rng: np.random.Generator,
    secret_length: int,
    challenge_length: int,
) -> tuple[int, ...]:
    return random_challenge(rng, secret_length, challenge_length)


def _rng(
    config: ChallengeSubsetConfig,
    domain: int,
    trial_index: int,
) -> np.random.Generator:
    return np.random.default_rng(
        np.random.SeedSequence([
            config.seed,
            domain,
            trial_index,
        ])
    )


def _new_keypad(
    config: ChallengeSubsetConfig,
    trial_index: int,
) -> SelectiveTowerShuffleKeypad:
    return SelectiveTowerShuffleKeypad.new_keypad(
        k=config.number_of_keys,
        p=config.icons_per_key,
        rng=_rng(config, 1, trial_index),
        tower_init_rng=_rng(config, 2, trial_index),
        extra_key_rng=_rng(config, 3, trial_index),
        rotation_rng=_rng(config, 4, trial_index),
        tower_floor_rng=_rng(config, 5, trial_index),
    )


def _new_scheduler(
    name: str,
    config: ChallengeSubsetConfig,
    trial_index: int,
) -> ChallengeScheduler:
    return new_challenge_scheduler(
        name=name,
        secret_length=config.secret_length,
        challenge_length=config.challenge_length,
        rng=_rng(config, 6, trial_index),
    )


def _run_trial(
    trial_index: int,
    challenge_schedule: str,
    secret: tuple[int, ...],
    config: ChallengeSubsetConfig,
) -> ChallengeSubsetTrial:
    keypad = _new_keypad(config, trial_index)
    scheduler = _new_scheduler(
        challenge_schedule,
        config,
        trial_index,
    )
    protocol = ChallengeSubsetProtocol(
        scheduler=scheduler,
        keypad=keypad,
    )
    attack = AttackState.unknown_secret(
        config.secret_length,
        config.total_icons,
    )
    observations_to_break = None
    observations_to_guaranteed_replay = None
    replay_success_curve = []
    position_coverage_curve = [0]
    challenges = []
    challenge_overlaps = []
    shuffle_results = []
    observed_positions: set[int] = set()
    previous_challenge: tuple[int, ...] | None = None

    for observation_count in range(config.max_observations + 1):
        active_challenge = protocol.current_challenge()
        challenge_positions = active_challenge.positions
        if observation_count <= config.curve_observations:
            replay_success_curve.append(
                attack.replay_success_probability(
                    keypad=keypad.keypad_mat(),
                    challenge_positions=challenge_positions,
                    max_tries=config.max_tries,
                )
            )
        if (
            observations_to_guaranteed_replay is None
            and attack.replay_support(
                keypad=keypad.keypad_mat(),
                challenge_positions=challenge_positions,
            ) <= config.max_tries
        ):
            observations_to_guaranteed_replay = observation_count

        if observation_count == config.max_observations:
            break

        challenged_icons = [
            secret[position]
            for position in challenge_positions
        ]
        key_selection = keypad.key_entry(challenged_icons)
        attack.observe(Observation(
            keypad=keypad.keypad_mat(),
            key_selection=key_selection,
            challenge_positions=challenge_positions,
        ))

        challenges.append(challenge_positions)
        if previous_challenge is None:
            challenge_overlaps.append(None)
        else:
            challenge_overlaps.append(len(
                set(previous_challenge) & set(challenge_positions)
            ))
        previous_challenge = challenge_positions
        observed_positions.update(challenge_positions)
        position_coverage_curve.append(len(observed_positions))

        completed_observations = observation_count + 1
        if (
            observations_to_break is None
            and attack.remaining_combinations <= config.max_tries
        ):
            observations_to_break = completed_observations
            if observations_to_guaranteed_replay is None:
                observations_to_guaranteed_replay = completed_observations

        advance = protocol.complete_success(
            challenge_id=active_challenge.challenge_id,
            selected_keys=key_selection,
        )
        shuffle_results.append(advance.shuffle_result)

    if observations_to_break is None:
        raise RuntimeError(
            f"{challenge_schedule} trial {trial_index} did not break within "
            f"{config.max_observations} observations"
        )
    if observations_to_guaranteed_replay is None:
        raise RuntimeError(
            f"{challenge_schedule} trial {trial_index} did not become "
            f"replayable within {config.max_observations} observations"
        )

    return ChallengeSubsetTrial(
        trial=trial_index,
        challenge_schedule=challenge_schedule,
        keypad_shuffle=SELECTIVE_TOWER,
        observations_to_break=observations_to_break,
        observations_to_guaranteed_replay=(
            observations_to_guaranteed_replay
        ),
        replay_success_curve=tuple(replay_success_curve),
        position_coverage_curve=tuple(position_coverage_curve),
        challenges=tuple(challenges),
        challenge_overlaps=tuple(challenge_overlaps),
        shuffle_results=tuple(shuffle_results),
    )


def run_challenge_subset_benchmark(
    config: ChallengeSubsetConfig,
    progress: ProgressCallback | None = None,
) -> ChallengeSubsetResult:
    trials = []
    for trial_index in range(config.run_count):
        secret = tuple(
            int(icon)
            for icon in _rng(config, 0, trial_index).choice(
                config.total_icons,
                size=config.secret_length,
                replace=False,
            )
        )
        for schedule in config.challenge_schedules:
            trials.append(_run_trial(
                trial_index=trial_index,
                challenge_schedule=schedule,
                secret=secret,
                config=config,
            ))
        if progress is not None:
            progress(trial_index + 1, config.run_count)
    return ChallengeSubsetResult(config=config, trials=tuple(trials))


def write_challenge_subset_artifacts(
    result: ChallengeSubsetResult,
    output_root: Path,
    overwrite: bool = False,
) -> Path:
    output_dir = output_root / result.config.run_name
    if output_dir.exists() and not overwrite:
        raise FileExistsError(
            f"{output_dir} already exists; use --overwrite to replace outputs"
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = result.summary()
    with (output_dir / "summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    with (output_dir / "trials.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "trial",
            "challenge_schedule",
            "keypad_shuffle",
            "observations_to_break",
            "observations_to_guaranteed_replay",
            "mean_rotation_keys",
            "mean_moved_icons",
            "mean_fixed_columns",
            "max_fixed_column_streak",
        ])
        for trial in result.trials:
            writer.writerow([
                trial.trial,
                trial.challenge_schedule,
                trial.keypad_shuffle,
                trial.observations_to_break,
                trial.observations_to_guaranteed_replay,
                trial.mean_rotation_keys,
                trial.mean_moved_icons,
                trial.mean_fixed_columns,
                trial.max_fixed_column_streak,
            ])

    with (output_dir / "replay_curve.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "observations",
            "challenge_schedule",
            "keypad_shuffle",
            "next_login_success_probability",
            "mean_positions_covered",
        ])
        for schedule in result.challenge_schedules:
            schedule_summary = summary["results"][
                schedule
            ][SELECTIVE_TOWER]
            for observation_count in range(
                result.config.curve_observations + 1
            ):
                writer.writerow([
                    observation_count,
                    schedule,
                    SELECTIVE_TOWER,
                    schedule_summary["next_login_success"][
                        str(observation_count)
                    ],
                    schedule_summary["position_coverage"][
                        str(observation_count)
                    ],
                ])

    with (output_dir / "transition_metrics.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "trial",
            "observation",
            "challenge_schedule",
            "keypad_shuffle",
            "challenge_positions",
            "consecutive_overlap",
            "positions_covered",
            "rotation_keys",
            "moved_icons",
            "fixed_column_count",
            "fixed_column_ids",
        ])
        for trial in result.trials:
            for observation_index, shuffle_result in enumerate(
                trial.shuffle_results,
                start=1,
            ):
                challenge = "|".join(
                    str(position + 1)
                    for position in trial.challenges[
                        observation_index - 1
                    ]
                )
                overlap = trial.challenge_overlaps[
                    observation_index - 1
                ]
                writer.writerow([
                    trial.trial,
                    observation_index,
                    trial.challenge_schedule,
                    trial.keypad_shuffle,
                    challenge,
                    "" if overlap is None else overlap,
                    trial.position_coverage_curve[observation_index],
                    len(shuffle_result.rotation_keys),
                    shuffle_result.moved_icons,
                    len(shuffle_result.fixed_columns),
                    "|".join(
                        str(column)
                        for column in shuffle_result.fixed_columns
                    ),
                ])

    _write_charts(result, output_dir)
    (output_dir / "report.md").write_text(
        _markdown_report(result, summary),
        encoding="utf-8",
    )
    return output_dir


def _write_charts(
    result: ChallengeSubsetResult,
    output_dir: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {
        UNIFORM: "#7d93d8",
        ALTERNATING_HALVES: "#ff5a1f",
    }
    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    for schedule in result.challenge_schedules:
        trials = result.trials_for(schedule)
        axes[0].hist(
            [trial.observations_to_break for trial in trials],
            bins=range(result.config.max_observations + 2),
            histtype="step",
            linewidth=2,
            label=schedule,
            color=colors[schedule],
        )
        axes[1].hist(
            [
                trial.observations_to_guaranteed_replay
                for trial in trials
            ],
            bins=range(result.config.max_observations + 2),
            histtype="step",
            linewidth=2,
            label=schedule,
            color=colors[schedule],
        )
    axes[0].set_title("Observations to crack")
    axes[1].set_title("Observations to guaranteed replay")
    for axis in axes:
        axis.set_xlabel("Completed observations")
        axis.set_ylabel("Trials")
        axis.legend()
        axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(output_dir / "observation_distributions.png", dpi=180)
    plt.close(figure)

    summary = result.summary()
    figure, axis = plt.subplots(figsize=(8, 5))
    for schedule in result.challenge_schedules:
        curve = summary["results"][
            schedule
        ][SELECTIVE_TOWER]["next_login_success"]
        observations = [int(value) for value in curve]
        probabilities = [curve[str(value)] * 100 for value in observations]
        axis.plot(
            observations,
            probabilities,
            marker="o",
            label=schedule,
            color=colors[schedule],
        )
    axis.set_title("Optimal three-try success on the next login")
    axis.set_xlabel("Completed observations")
    axis.set_ylabel("Success probability (%)")
    axis.set_ylim(0, 100)
    axis.grid(alpha=0.2)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "replay_probability.png", dpi=180)
    plt.close(figure)


def _markdown_report(
    result: ChallengeSubsetResult,
    summary: dict,
) -> str:
    config = result.config
    lines = [
        "# Challenge-Subset nKode: Scheduler Comparison",
        "",
        "## Configuration",
        "",
        f"- Trials per schedule: {config.run_count:,}",
        f"- Layout: {config.number_of_keys} keys × "
        f"{config.icons_per_key} icons",
        f"- Secret/challenge: {config.challenge_length}-of-"
        f"{config.secret_length}",
        f"- Keypad shuffle: `{SELECTIVE_TOWER}`",
        f"- Challenge schedules: "
        f"{', '.join(f'`{name}`' for name in result.challenge_schedules)}",
        f"- Attempt budget: {config.max_tries}",
        f"- Seed: `{config.seed}`",
        "",
        "The active challenge is used for both the replay calculation and the "
        "successful observed login. The keypad and scheduler advance once "
        "after that success.",
        "",
        "## Observation Results",
        "",
        "| Schedule | Metric | Mean | Median | P90 | P95 | Min | Max |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for schedule in result.challenge_schedules:
        schedule_summary = summary["results"][
            schedule
        ][SELECTIVE_TOWER]
        for label, key in (
            ("Crack", "break_observations"),
            ("Guaranteed replay", "guaranteed_replay_observations"),
        ):
            stats = schedule_summary[key]
            lines.append(
                f"| {schedule} | {label} | "
                f"{stats['mean']:.2f} | {stats['median']:.1f} | "
                f"{stats['p90']} | {stats['p95']} | "
                f"{stats['minimum']} | {stats['maximum']} |"
            )

    delta_key = f"{ALTERNATING_HALVES}_minus_{UNIFORM}"
    if delta_key in summary["paired_deltas"]:
        delta = summary["paired_deltas"][
            delta_key
        ][SELECTIVE_TOWER]
        lines.extend([
            "",
            "## Alternating-halves Minus Uniform",
            "",
            "| Metric | Mean delta | Median delta | P90 | P95 |",
            "|---|---:|---:|---:|---:|",
        ])
        for label, key in (
            ("Crack", "break_observations"),
            ("Guaranteed replay", "guaranteed_replay_observations"),
        ):
            stats = delta[key]
            lines.append(
                f"| {label} | {stats['mean']:.2f} | "
                f"{stats['median']:.1f} | {stats['p90']} | "
                f"{stats['p95']} |"
            )

    lines.extend([
        "",
        "## Selective-shuffle Metrics",
        "",
        "| Schedule | Mean overlap | Mean rotation keys | "
        "Mean moved icons | Mean fixed columns | "
        "Mean max fixed-column streak |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for schedule in result.challenge_schedules:
        values = summary["results"][schedule][SELECTIVE_TOWER]
        lines.append(
            f"| {schedule} | "
            f"{values['mean_consecutive_overlap']:.2f} | "
            f"{values['mean_rotation_keys']:.2f} | "
            f"{values['mean_moved_icons']:.2f} | "
            f"{values['mean_fixed_columns']:.2f} | "
            f"{values['mean_max_fixed_column_streak']:.2f} |"
        )

    lines.extend([
        "",
        "## Optimal three-try success on the next login",
        "",
        "| Observations | "
        + " | ".join(result.challenge_schedules)
        + " |",
        "|---:|" + "---:|" * len(result.challenge_schedules),
    ])
    for observation_count in range(config.curve_observations + 1):
        values = [
            summary["results"][schedule][
                SELECTIVE_TOWER
            ]["next_login_success"][str(observation_count)] * 100
            for schedule in result.challenge_schedules
        ]
        lines.append(
            f"| {observation_count} | "
            + " | ".join(f"{value:.2f}%" for value in values)
            + " |"
        )

    lines.extend([
        "",
        "## Method",
        "",
        "- A crack occurs when at most three full-secret candidates remain.",
        "- Guaranteed replay occurs when the active next challenge has at "
        "most three possible key sequences.",
        "- Replay probability sums the three most likely key sequences under "
        "the independent-position posterior.",
        "- Every successful observation adds one unpressed key to the "
        "distinct pressed keys and selectively advances the column tower.",
        "- Paired schedules use identical secrets, initial keypads, initial "
        "tower state, and domain-separated deterministic random streams.",
        "",
        "![Observation distributions](observation_distributions.png)",
        "",
        "![Replay probability](replay_probability.png)",
        "",
    ])
    return "\n".join(lines)
