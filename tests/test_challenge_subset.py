import csv
import json

import numpy as np
import pytest

from cli.challenge_subset_benchmark import _parser
from src.challenge_schedule import ALTERNATING_HALVES, UNIFORM
from src.challenge_subset import (
    SELECTIVE_TOWER,
    ChallengeSubsetConfig,
    _new_keypad,
    run_challenge_subset_benchmark,
    write_challenge_subset_artifacts,
)
from src.evilnkode import AttackState, Observation
from src.keypad.keypad import RandomShuffleKeypad
from src.utils import observations


def test_subset_observations_select_the_challenged_positions():
    keypad = RandomShuffleKeypad.new_keypad(
        k=6,
        p=8,
        rng=np.random.default_rng(7),
    )
    secret = [0, 8, 16, 24, 32, 40]
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


def test_challenge_subset_config_defaults_and_validation():
    config = ChallengeSubsetConfig()

    assert config.number_of_keys == 6
    assert config.icons_per_key == 8
    assert config.secret_length == 6
    assert config.challenge_length == 3
    assert config.challenge_schedules == (UNIFORM, ALTERNATING_HALVES)
    assert "shuffle-selective-tower" in config.run_name

    with pytest.raises(ValueError, match="exceed challenge_length"):
        ChallengeSubsetConfig(number_of_keys=3)
    with pytest.raises(ValueError, match="exactly twice"):
        ChallengeSubsetConfig(secret_length=7)
    with pytest.raises(ValueError, match="unknown challenge"):
        ChallengeSubsetConfig(challenge_schedules=("unknown",))


def test_challenge_subset_cli_defaults_to_both_schedules_and_eight_icons():
    args = _parser().parse_args([])

    assert args.icons_per_key == 8
    assert args.challenge_schedule == "all"


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
    assert first.challenge_schedules == (UNIFORM, ALTERNATING_HALVES)
    assert first.keypad_shuffles == (SELECTIVE_TOWER,)
    assert len(first.trials_for(UNIFORM)) == config.run_count
    assert len(first.trials_for(ALTERNATING_HALVES)) == config.run_count
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
        len(trial.replay_success_curve)
        == config.curve_observations + 1
        for trial in first.trials
    )
    assert all(
        len(trial.position_coverage_curve)
        == config.max_observations + 1
        for trial in first.trials
    )

    for trial in first.trials_for(ALTERNATING_HALVES):
        assert trial.challenges[:4] == (
            (0, 1, 2),
            (3, 4, 5),
            (0, 1, 2),
            (3, 4, 5),
        )
        assert trial.position_coverage_curve[:3] == (0, 3, 6)
        assert all(
            overlap == 0
            for overlap in trial.challenge_overlaps[1:]
        )

    for trial in first.trials:
        assert all(
            len(shuffle.rotation_keys)
            == len(shuffle.pressed_keys) + 1
            for shuffle in trial.shuffle_results
        )
        assert all(
            challenge == tuple(sorted(set(challenge)))
            and len(challenge) == config.challenge_length
            for challenge in trial.challenges
        )


def test_paired_schedules_receive_equal_but_independent_keypad_state():
    config = ChallengeSubsetConfig(run_count=1)
    first = _new_keypad(config, trial_index=0)
    second = _new_keypad(config, trial_index=0)
    second_layout = second.keypad.copy()
    second_left_tower = second.tower_shuffle.left_tower.tolist()

    assert first is not second
    assert np.array_equal(first.keypad, second.keypad)
    assert (
        first.tower_shuffle.left_tower.tolist()
        == second.tower_shuffle.left_tower.tolist()
    )

    first.shuffle([0, 0, 0])

    assert np.array_equal(second.keypad, second_layout)
    assert second.tower_shuffle.left_tower.tolist() == second_left_tower


def test_challenge_subset_can_run_one_schedule():
    config = ChallengeSubsetConfig(
        run_count=2,
        max_observations=30,
        curve_observations=2,
        challenge_schedules=(ALTERNATING_HALVES,),
    )

    result = run_challenge_subset_benchmark(config)

    assert result.challenge_schedules == (ALTERNATING_HALVES,)
    assert result.summary()["paired_deltas"] == {}


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
        "transition_metrics.csv",
        "trials.csv",
    }
    assert {path.name for path in output_dir.iterdir()} == expected_files
    assert all(
        (output_dir / filename).stat().st_size > 0
        for filename in expected_files
    )

    summary = json.loads((output_dir / "summary.json").read_text())
    assert summary["config"]["seed"] == config.seed
    assert set(summary["results"]) == {UNIFORM, ALTERNATING_HALVES}
    assert all(
        set(shuffles) == {SELECTIVE_TOWER}
        for shuffles in summary["results"].values()
    )

    with (output_dir / "trials.csv").open(newline="") as file:
        reader = csv.DictReader(file)
        assert reader.fieldnames == [
            "trial",
            "challenge_schedule",
            "keypad_shuffle",
            "observations_to_break",
            "observations_to_guaranteed_replay",
            "mean_rotation_keys",
            "mean_moved_icons",
            "mean_fixed_columns",
            "max_fixed_column_streak",
        ]
        assert len(list(reader)) == config.run_count * 2

    with (output_dir / "replay_curve.csv").open(newline="") as file:
        reader = csv.DictReader(file)
        assert reader.fieldnames == [
            "observations",
            "challenge_schedule",
            "keypad_shuffle",
            "next_login_success_probability",
            "mean_positions_covered",
        ]
        assert len(list(reader)) == (
            config.curve_observations + 1
        ) * 2

    with (output_dir / "transition_metrics.csv").open(newline="") as file:
        reader = csv.DictReader(file)
        assert reader.fieldnames == [
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
        ]
        assert len(list(reader)) == (
            config.max_observations * config.run_count * 2
        )

    report = (output_dir / "report.md").read_text()
    assert "Alternating-halves Minus Uniform" in report
    assert "Optimal three-try success" in report
    assert SELECTIVE_TOWER in report
