import csv
import itertools
import json
from collections import Counter

import numpy as np
import pytest

from src.challenge_subset import (
    ChallengeSubsetConfig,
    _random_challenge,
    run_challenge_subset_benchmark,
    write_challenge_subset_artifacts,
)
from src.evilnkode import AttackState, Observation
from src.keypad.keypad import RandomShuffleKeypad
from src.utils import observations


def test_random_challenges_cover_all_subsets_uniformly():
    rng = np.random.default_rng(1234)
    counts = Counter(
        _random_challenge(rng, secret_length=6, challenge_length=3)
        for _ in range(20_000)
    )

    assert set(counts) == set(itertools.combinations(range(6), 3))
    assert all(challenge == tuple(sorted(challenge)) for challenge in counts)
    assert min(counts.values()) >= 850
    assert max(counts.values()) <= 1_150


def test_subset_observations_select_the_challenged_positions():
    keypad = RandomShuffleKeypad.new_keypad(
        k=6,
        p=9,
        rng=np.random.default_rng(7),
    )
    secret = [0, 9, 18, 27, 36, 45]
    observation = next(observations(
        target_passcode=secret,
        keypad=keypad,
        number_of_observations=1,
        challenge_length=3,
        rng=np.random.default_rng(11),
    ))

    assert len(observation.positions) == 3
    assert len(set(observation.positions)) == 3
    assert observation.positions == tuple(sorted(observation.positions))
    assert observation.key_selection == keypad.key_entry([
        secret[position]
        for position in observation.positions
    ])


def test_attack_state_updates_only_challenged_positions():
    state = AttackState.unknown_secret(secret_length=6, total_icons=12)
    observation = Observation(
        keypad=[
            [0, 1, 2, 3],
            [4, 5, 6, 7],
            [8, 9, 10, 11],
        ],
        key_selection=[0, 1, 2],
        challenge_positions=(1, 4, 5),
    )

    state.observe(observation)

    assert state.candidates[0] == set(range(12))
    assert state.candidates[1] == {0, 1, 2, 3}
    assert state.candidates[2] == set(range(12))
    assert state.candidates[3] == set(range(12))
    assert state.candidates[4] == {4, 5, 6, 7}
    assert state.candidates[5] == {8, 9, 10, 11}


def test_legacy_observation_updates_every_secret_position():
    state = AttackState.unknown_secret(secret_length=3, total_icons=6)
    observation = Observation(
        keypad=[
            [0, 1],
            [2, 3],
            [4, 5],
        ],
        key_selection=[2, 0, 1],
    )

    state.observe(observation)

    assert observation.positions == (0, 1, 2)
    assert state.candidates == [{4, 5}, {0, 1}, {2, 3}]


def test_attack_state_calculates_optimal_replay_probability():
    state = AttackState(candidates=[
        {0, 1, 2},
        {0, 2},
    ])
    keypad = [[0, 1], [2, 3]]

    assert state.replay_support(keypad, (0, 1)) == 4
    assert state.replay_success_probability(
        keypad,
        challenge_positions=(0, 1),
        max_tries=3,
    ) == pytest.approx(5 / 6)


def test_challenge_subset_benchmark_is_seeded_and_paired():
    config = ChallengeSubsetConfig(
        run_count=8,
        max_observations=30,
        curve_observations=5,
        seed=99,
    )

    first = run_challenge_subset_benchmark(config)
    second = run_challenge_subset_benchmark(config)

    assert first == second
    assert len(first.trials_for("random")) == config.run_count
    assert len(first.trials_for("tower")) == config.run_count
    assert all(
        0 <= trial.observations_to_guaranteed_replay
        <= config.max_observations
        for trial in first.trials
    )
    assert all(
        1 <= trial.observations_to_break <= config.max_observations
        for trial in first.trials
    )
    assert all(
        len(trial.replay_success_curve) == config.curve_observations + 1
        for trial in first.trials
    )


def test_challenge_subset_artifacts(tmp_path):
    config = ChallengeSubsetConfig(
        run_count=6,
        max_observations=30,
        curve_observations=4,
        seed=101,
    )
    result = run_challenge_subset_benchmark(config)

    output_dir = write_challenge_subset_artifacts(result, tmp_path)

    expected_files = {
        "observation_distributions.png",
        "replay_curve.csv",
        "replay_probability.png",
        "report.md",
        "summary.json",
        "trials.csv",
    }
    assert {path.name for path in output_dir.iterdir()} == expected_files
    assert all(
        (output_dir / filename).stat().st_size > 0
        for filename in expected_files
    )

    summary = json.loads((output_dir / "summary.json").read_text())
    assert summary["config"]["seed"] == config.seed
    assert set(summary["shuffle_results"]) == {"random", "tower"}

    with (output_dir / "trials.csv").open(newline="") as file:
        reader = csv.DictReader(file)
        assert reader.fieldnames == [
            "trial",
            "shuffle",
            "observations_to_break",
            "observations_to_guaranteed_replay",
        ]
        assert len(list(reader)) == config.run_count * 2
    with (output_dir / "replay_curve.csv").open(newline="") as file:
        reader = csv.DictReader(file)
        assert reader.fieldnames == [
            "observations",
            "shuffle",
            "next_login_success_probability",
        ]
        assert len(list(reader)) == (
            config.curve_observations + 1
        ) * 2

    report = (output_dir / "report.md").read_text()
    assert "Tower Minus Random" in report
    assert "Optimal three-try success" in report
