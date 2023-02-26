from py_arkworks_bls12381 import G1Point, G2Point, Scalar, GT
from typing import Sequence, Tuple

# Copies the interface for py-ecc

# This is the identity point or point at infinity
Z1 = G1Point.identity()
# Generator point for G1
G1 = G1Point()
# Generator point for G2
G2 = G2Point()

def add(lhs : G1Point | G2Point, rhs : G1Point | G1Point) -> G1Point | G2Point:
    return lhs + rhs

def neg(point : G1Point | G2Point) -> G1Point | G2Point:
    return -point

def multiply(point : G1Point | G2Point, integer : int) -> G1Point | G2Point:
    int_as_bytes = integer.to_bytes(32, 'little')
    scalar = Scalar.from_le_bytes(int_as_bytes)
    return point * scalar

def pairing_check(values : Sequence[Tuple[G1Point, G2Point]]) -> bool:
    p_q_1, p_q_2 = values
    g1s = [p_q_1[0], p_q_2[0]]
    g2s = [p_q_1[1], p_q_2[1]]
    return GT.multi_pairing(g1s, g2s) == GT.one()

def G1_to_bytes48(point : G1Point) -> bytes:
    return point.to_compressed_bytes()

def G2_to_bytes96(point : G2Point) -> bytes:
    return point.to_compressed_bytes()

def bytes96_to_G2(bytes96) -> G1Point:
    # This will not do subgroup checks
    # If you want that then remove the `_unchecked` prefix
    return G2Point.from_compressed_bytes_unchecked(bytes96)

def bytes48_to_G1(bytes48) -> G1Point:
    # This will not do subgroup checks
    # If you want that then remove the `_unchecked` prefix
    return G1Point.from_compressed_bytes_unchecked(bytes48)


# Small test code to make sure it compiles and show
# you how to call the methods
bytes48 = G1_to_bytes48(G1Point())
g1_point = bytes48_to_G1(bytes48)

bytes96 = G2_to_bytes96(G2Point())
g2_point = bytes96_to_G2(bytes96)

neg_g1 = neg(g1_point)

expected_identity = add(neg_g1, g1_point)
assert expected_identity == G1Point.identity()

four_gen = multiply(G2, 4)
expected_four_gen = G2 + G2 + G2 + G2
assert expected_four_gen == four_gen

a = Scalar(20)
b = Scalar(30)
ok = pairing_check([
    [G1 * a, G2 * b],
    [G1 * -a, G2 * b]
])
assert ok