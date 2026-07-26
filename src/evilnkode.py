import math
from collections import Counter
from dataclasses import dataclass, field
from heapq import nlargest
from itertools import product
from typing import Iterator, Sequence


@dataclass
class Observation:
    keypad: list[list[int]]
    key_selection: list[int]
    challenge_positions: tuple[int, ...] | None = None

    def __post_init__(self):
        if self.challenge_positions is None:
            return
        if len(self.challenge_positions) != len(self.key_selection):
            raise ValueError(
                "challenge positions and key selections must have the same length"
            )
        if tuple(sorted(set(self.challenge_positions))) != self.challenge_positions:
            raise ValueError("challenge positions must be unique and ascending")

    @property
    def positions(self) -> tuple[int, ...]:
        if self.challenge_positions is None:
            return tuple(range(len(self.key_selection)))
        return self.challenge_positions

    @property
    def property_list(self) -> list[set[int]]:
        return [set(self.keypad[idx]) for idx in self.key_selection]

    @property
    def flat_keypad(self) -> list[int]:
        return [num for row in self.keypad for num in row]


@dataclass
class EvilOutput:
    iterations_to_break: int
    iterations_to_replay: int


@dataclass
class AttackState:
    candidates: list[set[int]]

    @classmethod
    def unknown_secret(cls, secret_length: int, total_icons: int) -> "AttackState":
        possible_icons = set(range(total_icons))
        return cls([
            possible_icons.copy()
            for _ in range(secret_length)
        ])

    @property
    def remaining_combinations(self) -> int:
        return math.prod(len(candidates) for candidates in self.candidates)

    def observe(self, observation: Observation) -> None:
        for position, observed_icons in zip(
            observation.positions,
            observation.property_list,
        ):
            if not 0 <= position < len(self.candidates):
                raise ValueError(f"challenge position out of range: {position}")
            self.candidates[position].intersection_update(observed_icons)

    @staticmethod
    def _key_by_icon(keypad: list[list[int]]) -> dict[int, int]:
        return {
            icon: key_idx
            for key_idx, key in enumerate(keypad)
            for icon in key
        }

    def replay_support(
        self,
        keypad: list[list[int]],
        challenge_positions: Sequence[int],
    ) -> int:
        key_by_icon = self._key_by_icon(keypad)
        return math.prod(
            len({
                key_by_icon[icon]
                for icon in self.candidates[position]
            })
            for position in challenge_positions
        )

    def replay_success_probability(
        self,
        keypad: list[list[int]],
        challenge_positions: Sequence[int],
        max_tries: int,
    ) -> float:
        if max_tries < 1:
            raise ValueError("max_tries must be positive")

        key_by_icon = self._key_by_icon(keypad)
        per_position_probabilities = []
        for position in challenge_positions:
            candidates = self.candidates[position]
            if not candidates:
                return 0.0
            key_counts = Counter(key_by_icon[icon] for icon in candidates)
            per_position_probabilities.append([
                count / len(candidates)
                for count in key_counts.values()
            ])

        sequence_probabilities = (
            math.prod(probabilities)
            for probabilities in product(*per_position_probabilities)
        )
        return min(1.0, sum(nlargest(max_tries, sequence_probabilities)))


@dataclass
class EvilNKode:
    observations: Iterator[Observation]
    passcode_len: int
    number_of_keys: int
    properties_per_key: int  # Called icons_per_group in nKode-rs.
    max_tries_before_lockout: int = 5
    possible_nkode: list[set[int]] = field(init=False, default_factory=list)
    attack_state: AttackState | None = field(init=False, default=None)

    def initialize(self):
        self.attack_state = AttackState.unknown_secret(
            secret_length=self.passcode_len,
            total_icons=self.number_of_keys * self.properties_per_key,
        )
        self.possible_nkode = self.attack_state.candidates

    @property
    def _possible_nkode_count(self) -> int:
        if self.attack_state is None:
            raise RuntimeError("EvilNKode has not been initialized")
        return self.attack_state.remaining_combinations

    def _apply_observation(self, obs: Observation):
        if self.attack_state is None:
            raise RuntimeError("EvilNKode has not been initialized")
        self.attack_state.observe(obs)

    def run(self) -> EvilOutput:
        self.initialize()
        iterations_to_replay = None
        for observation_count, obs in enumerate(self.observations, start=1):
            if iterations_to_replay is None:
                replay_possibilities = self.replay_attack(obs)
                if replay_possibilities <= self.max_tries_before_lockout:
                    iterations_to_replay = observation_count

            self._apply_observation(obs)

            if self._possible_nkode_count <= self.max_tries_before_lockout:
                if iterations_to_replay is None:
                    # Knowing the nKode enables replay on any subsequent layout.
                    iterations_to_replay = observation_count
                return EvilOutput(
                    iterations_to_break=observation_count,
                    iterations_to_replay=iterations_to_replay
                )
        raise Exception("error in Evilkode, observations stopped yielding")

    def replay_attack(self, obs: Observation) -> int:
        if self.attack_state is None:
            raise RuntimeError("EvilNKode has not been initialized")
        return self.attack_state.replay_support(
            keypad=obs.keypad,
            challenge_positions=obs.positions,
        )
