from src.tower_shuffle import TowerShuffle

def test_tower_shuffle():
    tower = TowerShuffle.new(19)
    print(tower)
    for _ in range(100):
        tower.shuffle()
        print(tower)
