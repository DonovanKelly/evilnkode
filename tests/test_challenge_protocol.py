from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import numpy as np
import pytest

from src.challenge_protocol import ChallengeSubsetProtocol
from src.challenge_schedule import AlternatingHalvesChallengeScheduler
from src.keypad.keypad import SelectiveTowerShuffleKeypad


def _protocol() -> ChallengeSubsetProtocol:
    keypad = SelectiveTowerShuffleKeypad.new_keypad(
        k=6,
        p=8,
        rng=np.random.default_rng(1),
        tower_init_rng=np.random.default_rng(2),
        extra_key_rng=np.random.default_rng(3),
        rotation_rng=np.random.default_rng(4),
        tower_floor_rng=np.random.default_rng(5),
    )
    return ChallengeSubsetProtocol(
        scheduler=AlternatingHalvesChallengeScheduler(),
        keypad=keypad,
    )


def test_failure_retry_refresh_and_abandonment_retain_active_state():
    protocol = _protocol()
    active = protocol.current_challenge()
    keypad = protocol.keypad.keypad.copy()
    left_tower = protocol.keypad.tower_shuffle.left_tower.tolist()

    for _event in ("failure", "retry", "refresh", "abandonment"):
        assert protocol.retain_active_challenge(
            active.challenge_id
        ) == active
        assert np.array_equal(protocol.keypad.keypad, keypad)
        assert (
            protocol.keypad.tower_shuffle.left_tower.tolist()
            == left_tower
        )


def test_expiry_replaces_only_the_challenge_identifier():
    protocol = _protocol()
    active = protocol.current_challenge()
    keypad = protocol.keypad.keypad.copy()
    left_tower = protocol.keypad.tower_shuffle.left_tower.tolist()

    replacement = protocol.replace_expired_challenge(active.challenge_id)

    assert replacement.challenge_id != active.challenge_id
    assert replacement.positions == active.positions
    assert np.array_equal(protocol.keypad.keypad, keypad)
    assert protocol.keypad.tower_shuffle.left_tower.tolist() == left_tower
    with pytest.raises(ValueError, match="stale"):
        protocol.retain_active_challenge(active.challenge_id)


def test_success_advances_once_and_duplicate_finish_is_idempotent():
    protocol = _protocol()
    active = protocol.current_challenge()
    selected_keys = [0, 0, 0]

    first = protocol.complete_success(
        challenge_id=active.challenge_id,
        selected_keys=selected_keys,
    )
    keypad_after_success = protocol.keypad.keypad.copy()
    left_tower_after_success = (
        protocol.keypad.tower_shuffle.left_tower.tolist()
    )
    duplicate = protocol.complete_success(
        challenge_id=active.challenge_id,
        selected_keys=[1, 2, 3],
    )

    assert duplicate == first
    assert first.completed_challenge == active
    assert first.next_challenge.positions == (3, 4, 5)
    assert protocol.current_challenge() == first.next_challenge
    assert np.array_equal(protocol.keypad.keypad, keypad_after_success)
    assert (
        protocol.keypad.tower_shuffle.left_tower.tolist()
        == left_tower_after_success
    )


def test_concurrent_duplicate_finishes_advance_once():
    protocol = _protocol()
    active = protocol.current_challenge()
    barrier = Barrier(3)

    def finish(selected_keys):
        barrier.wait()
        return protocol.complete_success(
            challenge_id=active.challenge_id,
            selected_keys=selected_keys,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(finish, [0, 0, 0])
        second = executor.submit(finish, [1, 2, 3])
        barrier.wait()
        first_result = first.result()
        second_result = second.result()

    assert first_result == second_result
    assert protocol.current_challenge() == first_result.next_challenge
    assert protocol.current_challenge().challenge_id == 1
    assert protocol.current_challenge().positions == (3, 4, 5)


def test_unknown_or_stale_success_is_rejected():
    protocol = _protocol()

    with pytest.raises(ValueError, match="stale"):
        protocol.complete_success(
            challenge_id=999,
            selected_keys=[0],
        )
