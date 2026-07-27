from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


UNIFORM = "uniform"
ALTERNATING_HALVES = "alternating-halves"
CHALLENGE_SCHEDULES = (UNIFORM, ALTERNATING_HALVES)


def _validate_lengths(secret_length: int, challenge_length: int) -> None:
    if secret_length < 1:
        raise ValueError("secret_length must be positive")
    if not 1 <= challenge_length <= secret_length:
        raise ValueError(
            "challenge_length must be between 1 and secret_length"
        )


def random_challenge(
    rng: np.random.Generator,
    secret_length: int,
    challenge_length: int,
) -> tuple[int, ...]:
    _validate_lengths(secret_length, challenge_length)
    return tuple(sorted(
        int(position)
        for position in rng.choice(
            secret_length,
            size=challenge_length,
            replace=False,
        )
    ))


class ChallengeScheduler(ABC):
    name: str

    @abstractmethod
    def current_challenge(self) -> tuple[int, ...]:
        raise NotImplementedError

    @abstractmethod
    def advance(self) -> tuple[int, ...]:
        raise NotImplementedError


@dataclass
class UniformChallengeScheduler(ChallengeScheduler):
    secret_length: int
    challenge_length: int
    rng: np.random.Generator = field(
        default_factory=np.random.default_rng,
        repr=False,
        compare=False,
    )
    name: str = field(init=False, default=UNIFORM)
    _current: tuple[int, ...] = field(init=False)

    def __post_init__(self) -> None:
        _validate_lengths(self.secret_length, self.challenge_length)
        self._current = self._draw()

    def _draw(self) -> tuple[int, ...]:
        return random_challenge(
            self.rng,
            self.secret_length,
            self.challenge_length,
        )

    def current_challenge(self) -> tuple[int, ...]:
        return self._current

    def advance(self) -> tuple[int, ...]:
        self._current = self._draw()
        return self._current


@dataclass
class AlternatingHalvesChallengeScheduler(ChallengeScheduler):
    secret_length: int = 6
    challenge_length: int = 3
    name: str = field(init=False, default=ALTERNATING_HALVES)
    _phase: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        _validate_lengths(self.secret_length, self.challenge_length)
        if self.secret_length != self.challenge_length * 2:
            raise ValueError(
                "alternating-halves requires the secret length to be exactly "
                "twice the challenge length"
            )

    def current_challenge(self) -> tuple[int, ...]:
        start = self._phase * self.challenge_length
        return tuple(range(start, start + self.challenge_length))

    def advance(self) -> tuple[int, ...]:
        self._phase = 1 - self._phase
        return self.current_challenge()


def new_challenge_scheduler(
    name: str,
    secret_length: int,
    challenge_length: int,
    rng: np.random.Generator | None = None,
) -> ChallengeScheduler:
    if name == UNIFORM:
        return UniformChallengeScheduler(
            secret_length=secret_length,
            challenge_length=challenge_length,
            rng=np.random.default_rng() if rng is None else rng,
        )
    if name == ALTERNATING_HALVES:
        return AlternatingHalvesChallengeScheduler(
            secret_length=secret_length,
            challenge_length=challenge_length,
        )
    raise ValueError(
        f"unknown challenge schedule {name!r}; "
        f"expected one of {CHALLENGE_SCHEDULES}"
    )
