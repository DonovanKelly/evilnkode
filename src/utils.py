from math import factorial, comb

def total_valid_nkode_states(k: int, p: int) -> int:
   return factorial(k) ** (p-1)

def total_shuffle_states(k: int, p: int) -> int:
    return comb(p, p // 2) * factorial(k)
