import math
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Observation:
    keypad: list[list[int]]
    key_selection: list[int]

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
class EvilNKode:
    observations: Iterator[Observation]
    passcode_len: int
    number_of_keys: int
    properties_per_key: int  # Called icons_per_group in nKode-rs.
    max_tries_before_lockout: int = 5
    possible_nkode: list[set[int]] = field(init=False, default_factory=list)

    def initialize(self):
        possible_values = set(range(self.number_of_keys * self.properties_per_key))
        self.possible_nkode = [possible_values.copy() for _ in range(self.passcode_len)]

    @property
    def _possible_nkode_count(self) -> int:
        return math.prod(len(possible_values) for possible_values in self.possible_nkode)

    def _apply_observation(self, obs: Observation):
        for idx, observed_values in enumerate(obs.property_list):
            self.possible_nkode[idx].intersection_update(observed_values)

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
        key_by_property = {
            prop: key_idx
            for key_idx, key in enumerate(obs.keypad)
            for prop in key
        }
        return math.prod(
            len({key_by_property[prop] for prop in possible_values})
            for possible_values in self.possible_nkode
        )
