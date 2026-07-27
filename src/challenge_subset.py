import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, median
from typing import Callable

import numpy as np

from src.evilnkode import AttackState, Observation
from src.keypad.keypad import (
    BaseKeypad,
    RandomShuffleKeypad,
    SlidingTowerShuffleKeypad,
)


KeypadFactory = type[BaseKeypad]
ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class ChallengeSubsetConfig:
    number_of_keys: int = 6
    icons_per_key: int = 9
    secret_length: int = 6
    challenge_length: int = 3
    max_tries: int = 3
    run_count: int = 10_000
    max_observations: int = 30
    curve_observations: int = 15
    seed: int = 20_260_725

    def __post_init__(self):
        if self.number_of_keys < 2:
            raise ValueError("number_of_keys must be at least 2")
        if self.icons_per_key < 1:
            raise ValueError("icons_per_key must be positive")
        if not 1 <= self.challenge_length <= self.secret_length:
            raise ValueError(
                "challenge_length must be between 1 and secret_length"
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

    @property
    def total_icons(self) -> int:
        return self.number_of_keys * self.icons_per_key

    @property
    def run_name(self) -> str:
        return (
            f"{self.challenge_length}of{self.secret_length}"
            f"-keys{self.number_of_keys}"
            f"-icons{self.icons_per_key}"
            f"-tries{self.max_tries}"
            f"-runs{self.run_count}"
            f"-seed{self.seed}"
        )


@dataclass(frozen=True)
class TrialScenario:
    secret: tuple[int, ...]
    observation_challenges: tuple[tuple[int, ...], ...]
    replay_challenges: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class ChallengeSubsetTrial:
    trial: int
    shuffle: str
    observations_to_break: int
    observations_to_guaranteed_replay: int
    replay_success_curve: tuple[float, ...]


@dataclass(frozen=True)
class ChallengeSubsetResult:
    config: ChallengeSubsetConfig
    trials: tuple[ChallengeSubsetTrial, ...]

    def trials_for(self, shuffle: str) -> list[ChallengeSubsetTrial]:
        return [trial for trial in self.trials if trial.shuffle == shuffle]

    @property
    def shuffles(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(trial.shuffle for trial in self.trials))

    def summary(self) -> dict:
        shuffle_summaries = {}
        for shuffle in self.shuffles:
            trials = self.trials_for(shuffle)
            shuffle_summaries[shuffle] = {
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
            }

        paired_by_shuffle = {
            shuffle: {
                trial.trial: trial
                for trial in self.trials_for(shuffle)
            }
            for shuffle in self.shuffles
        }
        random_trials = paired_by_shuffle["random"]
        tower_trials = paired_by_shuffle["tower"]
        paired_trial_ids = sorted(set(random_trials) & set(tower_trials))

        return {
            "config": asdict(self.config),
            "shuffle_results": shuffle_summaries,
            "tower_minus_random": {
                "break_observations": _summary_statistics([
                    tower_trials[trial_id].observations_to_break
                    - random_trials[trial_id].observations_to_break
                    for trial_id in paired_trial_ids
                ]),
                "guaranteed_replay_observations": _summary_statistics([
                    tower_trials[
                        trial_id
                    ].observations_to_guaranteed_replay
                    - random_trials[
                        trial_id
                    ].observations_to_guaranteed_replay
                    for trial_id in paired_trial_ids
                ]),
            },
        }


def _nearest_rank(values: list[int], probability: float) -> int:
    ordered = sorted(values)
    return ordered[math.ceil(probability * len(ordered)) - 1]


def _summary_statistics(values: list[int]) -> dict[str, float | int]:
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
    return tuple(sorted(
        int(position)
        for position in rng.choice(
            secret_length,
            size=challenge_length,
            replace=False,
        )
    ))


def _new_scenario(
    config: ChallengeSubsetConfig,
    rng: np.random.Generator,
) -> TrialScenario:
    secret = tuple(
        int(icon)
        for icon in rng.choice(
            config.total_icons,
            size=config.secret_length,
            replace=False,
        )
    )
    observation_challenges = tuple(
        _random_challenge(
            rng,
            config.secret_length,
            config.challenge_length,
        )
        for _ in range(config.max_observations)
    )
    replay_challenges = tuple(
        _random_challenge(
            rng,
            config.secret_length,
            config.challenge_length,
        )
        for _ in range(config.max_observations + 1)
    )
    return TrialScenario(
        secret=secret,
        observation_challenges=observation_challenges,
        replay_challenges=replay_challenges,
    )


def _run_trial(
    trial_index: int,
    shuffle_name: str,
    keypad_factory: KeypadFactory,
    scenario: TrialScenario,
    config: ChallengeSubsetConfig,
    rng: np.random.Generator,
) -> ChallengeSubsetTrial:
    keypad = keypad_factory.new_keypad(
        config.number_of_keys,
        config.icons_per_key,
        rng=rng,
    )
    attack = AttackState.unknown_secret(
        config.secret_length,
        config.total_icons,
    )
    observations_to_break = None
    observations_to_guaranteed_replay = None
    replay_success_curve = []

    for observation_count in range(config.max_observations + 1):
        replay_challenge = scenario.replay_challenges[observation_count]
        if observation_count <= config.curve_observations:
            replay_success_curve.append(
                attack.replay_success_probability(
                    keypad=keypad.keypad_mat(),
                    challenge_positions=replay_challenge,
                    max_tries=config.max_tries,
                )
            )
        if (
            observations_to_guaranteed_replay is None
            and attack.replay_support(
                keypad=keypad.keypad_mat(),
                challenge_positions=replay_challenge,
            ) <= config.max_tries
        ):
            observations_to_guaranteed_replay = observation_count

        if observation_count == config.max_observations:
            break

        challenge_positions = scenario.observation_challenges[observation_count]
        challenged_icons = [
            scenario.secret[position]
            for position in challenge_positions
        ]
        observation = Observation(
            keypad=keypad.keypad_mat(),
            key_selection=keypad.key_entry(challenged_icons),
            challenge_positions=challenge_positions,
        )
        attack.observe(observation)

        completed_observations = observation_count + 1
        if (
            observations_to_break is None
            and attack.remaining_combinations <= config.max_tries
        ):
            observations_to_break = completed_observations
            if observations_to_guaranteed_replay is None:
                observations_to_guaranteed_replay = completed_observations

        keypad.shuffle()

    if observations_to_break is None:
        raise RuntimeError(
            f"{shuffle_name} trial {trial_index} did not break within "
            f"{config.max_observations} observations"
        )
    if observations_to_guaranteed_replay is None:
        raise RuntimeError(
            f"{shuffle_name} trial {trial_index} did not become replayable "
            f"within {config.max_observations} observations"
        )

    return ChallengeSubsetTrial(
        trial=trial_index,
        shuffle=shuffle_name,
        observations_to_break=observations_to_break,
        observations_to_guaranteed_replay=observations_to_guaranteed_replay,
        replay_success_curve=tuple(replay_success_curve),
    )


def run_challenge_subset_benchmark(
    config: ChallengeSubsetConfig,
    progress: ProgressCallback | None = None,
) -> ChallengeSubsetResult:
    scenario_rng = np.random.default_rng(
        np.random.SeedSequence([config.seed, 0])
    )
    shuffle_factories = (
        ("random", RandomShuffleKeypad),
        ("tower", SlidingTowerShuffleKeypad),
    )
    trials = []
    for trial_index in range(config.run_count):
        scenario = _new_scenario(config, scenario_rng)
        for shuffle_index, (shuffle_name, keypad_factory) in enumerate(
            shuffle_factories,
            start=1,
        ):
            shuffle_rng = np.random.default_rng(
                np.random.SeedSequence([
                    config.seed,
                    shuffle_index,
                    trial_index,
                ])
            )
            trials.append(_run_trial(
                trial_index=trial_index,
                shuffle_name=shuffle_name,
                keypad_factory=keypad_factory,
                scenario=scenario,
                config=config,
                rng=shuffle_rng,
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
            "shuffle",
            "observations_to_break",
            "observations_to_guaranteed_replay",
        ])
        for trial in result.trials:
            writer.writerow([
                trial.trial,
                trial.shuffle,
                trial.observations_to_break,
                trial.observations_to_guaranteed_replay,
            ])

    with (output_dir / "replay_curve.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow([
            "observations",
            "shuffle",
            "next_login_success_probability",
        ])
        for shuffle in result.shuffles:
            curve = summary["shuffle_results"][
                shuffle
            ]["next_login_success"]
            for observation_count, probability in curve.items():
                writer.writerow([
                    observation_count,
                    shuffle,
                    probability,
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

    colors = {"random": "#7d93d8", "tower": "#ff5a1f"}
    figure, axes = plt.subplots(1, 2, figsize=(12, 5))
    for shuffle in result.shuffles:
        trials = result.trials_for(shuffle)
        axes[0].hist(
            [trial.observations_to_break for trial in trials],
            bins=range(result.config.max_observations + 2),
            histtype="step",
            linewidth=2,
            label=shuffle,
            color=colors[shuffle],
        )
        axes[1].hist(
            [
                trial.observations_to_guaranteed_replay
                for trial in trials
            ],
            bins=range(result.config.max_observations + 2),
            histtype="step",
            linewidth=2,
            label=shuffle,
            color=colors[shuffle],
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
    for shuffle in result.shuffles:
        curve = summary["shuffle_results"][
            shuffle
        ]["next_login_success"]
        observations = [int(value) for value in curve]
        probabilities = [curve[str(value)] * 100 for value in observations]
        axis.plot(
            observations,
            probabilities,
            marker="o",
            label=shuffle,
            color=colors[shuffle],
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
        "# Challenge-Subset nKode: 3-of-6 Shuffle Comparison",
        "",
        "## Configuration",
        "",
        f"- Trials per shuffle: {config.run_count:,}",
        f"- Layout: {config.number_of_keys} keys × "
        f"{config.icons_per_key} icons",
        f"- Secret/challenge: {config.challenge_length}-of-"
        f"{config.secret_length}",
        f"- Attempt budget: {config.max_tries}",
        f"- Seed: `{config.seed}`",
        "",
        "Each challenge is a uniformly random subset of distinct secret "
        "positions, entered in ascending position order.",
        "",
        "## Observation Results",
        "",
        "| Shuffle | Metric | Mean | Median | P90 | P95 | Min | Max |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for shuffle in result.shuffles:
        shuffle_summary = summary["shuffle_results"][shuffle]
        for label, key in (
            ("Crack", "break_observations"),
            ("Guaranteed replay", "guaranteed_replay_observations"),
        ):
            stats = shuffle_summary[key]
            lines.append(
                f"| {shuffle.title()} | {label} | "
                f"{stats['mean']:.2f} | {stats['median']:.1f} | "
                f"{stats['p90']} | {stats['p95']} | "
                f"{stats['minimum']} | {stats['maximum']} |"
            )

    delta = summary["tower_minus_random"]
    lines.extend([
        "",
        "## Tower Minus Random",
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
        "## Optimal three-try success on the next login",
        "",
        "| Observations | Random | Tower |",
        "|---:|---:|---:|",
    ])
    random_curve = summary["shuffle_results"][
        "random"
    ]["next_login_success"]
    tower_curve = summary["shuffle_results"][
        "tower"
    ]["next_login_success"]
    for observation_count in range(config.curve_observations + 1):
        lines.append(
            f"| {observation_count} | "
            f"{random_curve[str(observation_count)] * 100:.2f}% | "
            f"{tower_curve[str(observation_count)] * 100:.2f}% |"
        )

    lines.extend([
        "",
        "## Method",
        "",
        "- A crack occurs when at most three full-secret candidates remain.",
        "- Guaranteed replay occurs when a random next challenge has at most "
        "three possible key sequences.",
        "- Replay probability sums the three most likely key sequences under "
        "the independent-position posterior.",
        "- Both shuffles use identical secrets and challenge sequences for "
        "each paired trial.",
        "",
        "![Observation distributions](observation_distributions.png)",
        "",
        "![Replay probability](replay_probability.png)",
        "",
    ])
    return "\n".join(lines)
