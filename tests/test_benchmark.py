from src.benchmark import passcode_generator
import pytest

@pytest.mark.parametrize(
    "k, p, n, c, d, runs",
    [
        (6, 9, 4, 4, 4, 100)
    ]
)
def test_passcode_generator(k, p, n, c, d, runs):
    for _ in range(runs):
        passcode = passcode_generator(k=k, p=p, n=n, c=c, d=d)
        passcode_sets = [el//p for el in passcode]
        assert  c <= len(set(passcode))
        assert d <= len(set(passcode_sets))
