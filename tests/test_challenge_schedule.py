import itertools
from collections import Counter

import numpy as np
import pytest

from src.challenge_schedule import (
    ALTERNATING_HALVES,
    CHALLENGE_SCHEDULES,
    UNIFORM,
    AlternatingHalvesChallengeScheduler,
    UniformChallengeScheduler,
    new_challenge_scheduler,
    random_challenge,
)


def test_random_challenges_cover_all_subsets_uniformly():
    rng = np.random.default_rng(1234)
    counts = Counter(
        random_challenge(rng, secret_length=6, challenge_length=3)
        for _ in range(20_000)
    )

    assert set(counts) == set(itertools.combinations(range(6), 3))
    assert all(challenge == tuple(sorted(challenge)) for challenge in counts)
    assert min(counts.values()) >= 850
    assert max(counts.values()) <= 1_150


def test_uniform_subset_overlap_distribution_is_one_nine_nine_one():
    current = {0, 1, 2}
    counts = Counter(
        len(current & set(challenge))
        for challenge in itertools.combinations(range(6), 3)
    )

    assert counts == {0: 1, 1: 9, 2: 9, 3: 1}


def test_uniform_challenge_is_stable_until_advance():
    scheduler = UniformChallengeScheduler(
        secret_length=6,
        challenge_length=3,
        rng=np.random.default_rng(55),
    )

    active = scheduler.current_challenge()

    assert scheduler.current_challenge() is active
    assert scheduler.current_challenge() == active
    assert scheduler.advance() == scheduler.current_challenge()
    assert len(scheduler.current_challenge()) == 3


def test_alternating_halves_advance_only_when_called():
    scheduler = AlternatingHalvesChallengeScheduler()

    assert scheduler.current_challenge() == (0, 1, 2)
    assert scheduler.current_challenge() == (0, 1, 2)
    assert scheduler.advance() == (3, 4, 5)
    assert scheduler.current_challenge() == (3, 4, 5)
    assert scheduler.advance() == (0, 1, 2)


def test_challenge_scheduler_factory_and_validation():
    assert CHALLENGE_SCHEDULES == (UNIFORM, ALTERNATING_HALVES)
    assert new_challenge_scheduler(
        UNIFORM,
        secret_length=6,
        challenge_length=3,
        rng=np.random.default_rng(1),
    ).name == UNIFORM
    assert new_challenge_scheduler(
        ALTERNATING_HALVES,
        secret_length=6,
        challenge_length=3,
    ).name == ALTERNATING_HALVES

    with pytest.raises(ValueError, match="exactly twice"):
        AlternatingHalvesChallengeScheduler(
            secret_length=7,
            challenge_length=3,
        )
    with pytest.raises(ValueError, match="unknown challenge schedule"):
        new_challenge_scheduler(
            "unknown",
            secret_length=6,
            challenge_length=3,
        )
