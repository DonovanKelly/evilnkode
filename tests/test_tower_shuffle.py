import numpy as np

from src.keypad.tower_shuffle import Tower, TowerShuffle


def test_tower_appends_incoming_floor():
    tower = Tower(floors=[
        np.array([2, 0, 1]),
        np.array([4, 3]),
    ])

    tower.update_tower(
        keep=np.array([1, 2, 3]),
        other_discard=np.array([5, 6]),
    )

    assert [floor.tolist() for floor in tower.floors] == [[2, 1], [3], [5, 6]]


def test_tower_shuffle():
    tower = TowerShuffle.new(9)
    print(tower)
    for _ in range(100):
        tower.shuffle()
        print(tower)
