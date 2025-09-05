import random
import pytest

from src.evilkode import Evilkode, Observation
from src.keypad import Keypad


@pytest.fixture
def observations(number_of_keys, properties_per_key, passcode_len):
    k = number_of_keys
    p = properties_per_key
    n = passcode_len
    nkode = [random.randint(0, k*p-1) for _ in range(n)]
    keypad = Keypad.new_keypad(k, p)

    def obs_gen():
        for _ in range(100):  # finite number of yields
            yield Observation(
                keypad=keypad.keypad.copy(),
                key_selection=keypad.key_entry(target_passcode=nkode)
            )
            keypad.split_shuffle()

    return obs_gen()



@pytest.mark.parametrize(
    "number_of_keys, properties_per_key, passcode_len",
    [
        (5, 3, 4),  # Test case 1
        (10, 5, 6),  # Test case 2
        (8, 4, 5),   # Test case 3
    ]
)
def test_evilkode(number_of_keys, properties_per_key, passcode_len, observations):
    evilkode = Evilkode(
        observations=observations,
        number_of_keys=number_of_keys,
        properties_per_key=properties_per_key,
        passcode_len=passcode_len,
    )

    evilout = evilkode.run()
    assert evilout.iterations_to_break > 1
