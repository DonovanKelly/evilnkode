from dataclasses import dataclass, field
from threading import Lock
from typing import Sequence

from src.challenge_schedule import ChallengeScheduler
from src.keypad.keypad import (
    SelectiveShuffleResult,
    SelectiveTowerShuffleKeypad,
)


@dataclass(frozen=True)
class ActiveChallenge:
    challenge_id: int
    positions: tuple[int, ...]


@dataclass(frozen=True)
class SuccessfulChallengeAdvance:
    completed_challenge: ActiveChallenge
    next_challenge: ActiveChallenge
    shuffle_result: SelectiveShuffleResult


@dataclass
class ChallengeSubsetProtocol:
    scheduler: ChallengeScheduler
    keypad: SelectiveTowerShuffleKeypad
    _next_challenge_id: int = field(init=False, default=1)
    _active: ActiveChallenge = field(init=False)
    _completed: dict[int, SuccessfulChallengeAdvance] = field(
        init=False,
        default_factory=dict,
    )
    _lock: object = field(
        init=False,
        default_factory=Lock,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        self._active = ActiveChallenge(
            challenge_id=0,
            positions=self.scheduler.current_challenge(),
        )

    def current_challenge(self) -> ActiveChallenge:
        return self._active

    def retain_active_challenge(
        self,
        challenge_id: int,
    ) -> ActiveChallenge:
        with self._lock:
            self._require_active(challenge_id)
            return self._active

    def replace_expired_challenge(
        self,
        challenge_id: int,
    ) -> ActiveChallenge:
        with self._lock:
            self._require_active(challenge_id)
            self._active = self._new_active(
                positions=self._active.positions,
            )
            return self._active

    def complete_success(
        self,
        challenge_id: int,
        selected_keys: Sequence[int],
    ) -> SuccessfulChallengeAdvance:
        with self._lock:
            completed = self._completed.get(challenge_id)
            if completed is not None:
                return completed
            self._require_active(challenge_id)

            completed_challenge = self._active
            shuffle_result = self.keypad.shuffle(selected_keys)
            next_positions = self.scheduler.advance()
            self._active = self._new_active(positions=next_positions)
            advance = SuccessfulChallengeAdvance(
                completed_challenge=completed_challenge,
                next_challenge=self._active,
                shuffle_result=shuffle_result,
            )
            self._completed[challenge_id] = advance
            return advance

    def _new_active(
        self,
        positions: tuple[int, ...],
    ) -> ActiveChallenge:
        challenge = ActiveChallenge(
            challenge_id=self._next_challenge_id,
            positions=positions,
        )
        self._next_challenge_id += 1
        return challenge

    def _require_active(self, challenge_id: int) -> None:
        if challenge_id != self._active.challenge_id:
            raise ValueError(
                f"challenge {challenge_id} is stale; "
                f"active challenge is {self._active.challenge_id}"
            )
