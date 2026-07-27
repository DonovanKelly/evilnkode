# Two-Key vs. Three-Key Rotation

## Question

When all three challenged icons are currently on the same keypad key, does
adding one other key and rotating two keys provide the same useful mixing as
adding two other keys and rotating three keys?

This example writes out both rotations on a 6-key keypad with 8 icons per key.
It also separates the two possible interpretations of a two-key rotation:

1. swap both column towers; or
2. swap one column tower and leave the other tower fixed.

That distinction determines whether two and three keys behave differently.

## Starting keypad

The icon columns are split into two tower sides:

```text
left columns  = C0, C2, C4, C6
right columns = C1, C3, C5, C7
```

The starting keypad is:

| Key | C0 L | C1 R | C2 L | C3 R | C4 L | C5 R | C6 L | C7 R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| K0 | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| K1 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| K2 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
| K3 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
| K4 | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 |
| K5 | 40 | 41 | 42 | 43 | 44 | 45 | 46 | 47 |

Suppose the challenged secret icons are `0`, `1`, and `2`. All three are on
`K0`, so the observed entry is:

```text
K0, K0, K0
```

Rows outside the chosen rotation set remain untouched in every example.

## Idea 1A: two keys, swap both tower sides

Choose `K1` as the one additional key. The rotation set is:

```text
S = [K0, K1]
```

There is only one nonzero cyclic rotation of two keys:

```text
K0 <-> K1
```

Apply that swap to both the left and right column towers:

| Key | C0 L | C1 R | C2 L | C3 R | C4 L | C5 R | C6 L | C7 R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| K0 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| K1 | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
| K2 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
| K3 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
| K4 | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 |
| K5 | 40 | 41 | 42 | 43 | 44 | 45 | 46 | 47 |

The challenged icons move as follows:

```text
0: K0 -> K1
1: K0 -> K1
2: K0 -> K1
```

All eight candidate icons previously observed on `K0` also move to `K1`.
Every icon in the two selected rows moves, but the column-tower split has no
effect on their destination. The two tower sides perform the same operation.

## Idea 1B: two keys, swap one side and keep one side fixed

Two keys can produce different behavior for the tower sides if identity is
allowed as one of the rotations:

```text
left columns:  K0 <-> K1
right columns: no movement
```

The resulting keypad is:

| Key | C0 L | C1 R | C2 L | C3 R | C4 L | C5 R | C6 L | C7 R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| K0 | 8 | 1 | 10 | 3 | 12 | 5 | 14 | 7 |
| K1 | 0 | 9 | 2 | 11 | 4 | 13 | 6 | 15 |
| K2 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
| K3 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
| K4 | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 |
| K5 | 40 | 41 | 42 | 43 | 44 | 45 | 46 | 47 |

The challenged icons move as follows:

```text
0: K0 -> K1  (left tower)
1: K0 -> K0  (right tower)
2: K0 -> K1  (left tower)
```

The old `K0` candidate set now spans two destination keys:

```text
left-column candidates  -> K1
right-column candidates -> K0
```

This preserves two possible destinations, but icons in the fixed tower do not
rotate. A challenged icon is therefore not guaranteed to move.

## Idea 2: three keys, two distinct nonzero rotations

Choose `K1` and `K2` as the two additional keys:

```text
S = [K0, K1, K2]
```

Three keys have two distinct nonzero cyclic rotations. Use:

```text
left columns:  shift +1
K0 -> K1 -> K2 -> K0

right columns: shift +2
K0 -> K2 -> K1 -> K0
```

The resulting keypad is:

| Key | C0 L | C1 R | C2 L | C3 R | C4 L | C5 R | C6 L | C7 R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| K0 | 16 | 9 | 18 | 11 | 20 | 13 | 22 | 15 |
| K1 | 0 | 17 | 2 | 19 | 4 | 21 | 6 | 23 |
| K2 | 8 | 1 | 10 | 3 | 12 | 5 | 14 | 7 |
| K3 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
| K4 | 32 | 33 | 34 | 35 | 36 | 37 | 38 | 39 |
| K5 | 40 | 41 | 42 | 43 | 44 | 45 | 46 | 47 |

The challenged icons move as follows:

```text
0: K0 -> K1  (left tower)
1: K0 -> K2  (right tower)
2: K0 -> K1  (left tower)
```

The old `K0` candidate set again spans two destination keys:

```text
left-column candidates  -> K1
right-column candidates -> K2
```

Unlike the swap-plus-identity version, every icon in the three selected rows
moves because both rotations are nonzero.

## Direct comparison

| Property | 2 keys: swap both | 2 keys: swap + identity | 3 keys: two nonzero shifts |
|---|---:|---:|---:|
| Key rows touched | 2 | 2 | 3 |
| Different action per tower side | No | Yes | Yes |
| Every icon in the rotation set moves | Yes | No | Yes |
| Old `K0` candidates split across two keys | No | Yes | Yes |
| Preserves two distinct nonzero tower rotations | No | No | Yes |

## Conclusion

Two and three keys **do provide the same number of candidate destinations** if
the two-key design permits one tower side to remain fixed. In that sense, the
intuition that they can provide equivalent ambiguity is correct.

They differ only when both of these properties are required simultaneously:

1. every icon in the rotation set must move; and
2. the two column towers must use different rotations.

Two keys cannot satisfy both properties: their only nonzero rotation is the
single swap. Three keys can satisfy both by assigning `+1` and `+2` to the two
column towers.
