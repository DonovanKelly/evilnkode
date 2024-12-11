import math
from dataclasses import dataclass
from itertools import chain
from typing import Iterator


@dataclass
class Observation:
    keypad: list[list[int]]
    key_selection: list[int]

    @property
    def property_list(self) -> list[set[int]]:
        return [set(self.keypad[idx]) for idx in self.key_selection]


@dataclass
class EvilOutput:
    possible_nkodes: list[list[int]]
    iterations: int

    @property
    def number_of_possible_nkode(self):
        return math.prod([len(el) for el in self.possible_nkodes])


@dataclass
class Evilkode:
    observations: Iterator[Observation]
    passcode_len: int
    number_of_keys: int
    properties_per_key: int
    max_tries_before_lockout: int = 5
    possible_nkode = None


    def initialize(self):
        possible_values = set(range(self.number_of_keys * self.properties_per_key))
        self.possible_nkode = [possible_values.copy() for _ in range(self.passcode_len)]

    def run(self) -> EvilOutput:
        self.initialize()
        for idx, obs in enumerate(self.observations):
            if math.prod([len(el) for el in self.possible_nkode]) <= self.max_tries_before_lockout:
                return EvilOutput(possible_nkodes=[list(el) for el in self.possible_nkode], iterations=idx+1)
            for jdx, props in enumerate(obs.property_list):
                self.possible_nkode[jdx] = props.intersection(self.possible_nkode[jdx])

        raise Exception("error in Evilkode, observations stopped yielding")
