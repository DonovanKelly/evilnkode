from dataclasses import dataclass, field
import numpy as np


@dataclass
class Tower:
    floors: list[np.ndarray]

    def split_tower(
        self,
        rng: np.random.Generator | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        if rng is None:
            rng = np.random.default_rng()
        discard = np.array([], dtype=int)
        keep = np.array([], dtype=int)
        balance = self.balance(rng)
        for idx, floor in enumerate(self.floors):
            div = len(floor)//2 + balance[idx]
            floor_shuffle = rng.permutation(len(floor))
            keep = np.concatenate((keep, floor[floor_shuffle[:div]]))
            discard = np.concatenate((discard, floor[floor_shuffle[div:]]))
        diff = len(discard) - len(keep)
        assert abs(diff) <= 1
        return keep, discard

    def balance(self, rng: np.random.Generator | None = None) -> list[int]:
        if rng is None:
            rng = np.random.default_rng()
        odd_floors = np.array([
            idx
            for idx, floor in enumerate(self.floors)
            if len(floor) & 1
        ])
        balance = np.zeros(len(self.floors), dtype=int)
        if len(odd_floors) == 0:
            return balance.tolist()
        shuffle = rng.permutation(len(odd_floors))[:len(odd_floors) // 2]
        odd_floors = odd_floors[shuffle]
        balance[odd_floors] = 1
        return balance.tolist()


    def update_tower(self, keep: np.ndarray, other_discard: np.ndarray):
        new_floors = []
        for floor in self.floors:
            new_floor = floor[np.isin(floor, keep)]
            if len(new_floor):
                new_floors.append(new_floor)
        self.floors = new_floors
        self.floors.append(other_discard)

    def __str__(self):
        str_val = ""
        floor_numb = [i for i in reversed(range(len(self.floors)))]
        for idx, val in enumerate(reversed(self.floors)):
            str_val += f"Floor {floor_numb[idx]}: {val.tolist()}\n"
        return str_val

    def tolist(self) -> list[int]:
        tower = []
        for floor in self.floors:
            tower.extend(floor.tolist())
        return tower

@dataclass
class TowerShuffle:
    left_tower: Tower
    right_tower: Tower
    rng: np.random.Generator = field(
        default_factory=np.random.default_rng,
        repr=False,
        compare=False,
    )

    @classmethod
    def new(
        cls,
        total_pos: int,
        rng: np.random.Generator | None = None,
    ):
        assert total_pos >= 3
        if rng is None:
            rng = np.random.default_rng()
        rand_pos = rng.permutation(total_pos)
        return cls(
            left_tower=Tower(floors=[rand_pos[:total_pos//2]]),
            right_tower=Tower(floors=[rand_pos[total_pos//2:]]),
            rng=rng,
        )

    def shuffle(self, rng: np.random.Generator | None = None):
        if rng is None:
            rng = self.rng
        left_keep, left_discard = self.left_tower.split_tower(rng)
        right_keep, right_discard = self.right_tower.split_tower(rng)
        self.left_tower.update_tower(left_keep, right_discard)
        self.right_tower.update_tower(right_keep, left_discard)

    def __str__(self):
        return f"""Left Tower:
{self.left_tower}
Right Tower:
{self.right_tower}"""
