import numpy as np

from src.keypad import Keypad

def test_keypad():
    keypad = Keypad(
        keypad=np.array([
            [8, 9, 10, 11],
            [0, 5, 2, 3],
            [4, 1, 6,7]
        ]), k= 3, p=4, keypad_cache=[])

    assert keypad.key_entry([8, 5, 6, 11]) == [0,1,2,0]

def test_shuffle():
    p = 4  # properties_per_key
    k = 3  # number_of_keys
    keypad = Keypad.new_keypad(k, p)
    print(keypad.keypad)
    keypad.partial_shuffle()
    print(keypad.keypad)
    keypad.partial_shuffle()
    print(keypad.keypad)