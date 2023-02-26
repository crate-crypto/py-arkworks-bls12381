from py_ecc.bls import G2ProofOfPossession as py_ecc_bls
from py_ecc.optimized_bls12_381 import (  # noqa: F401
    G1,
    G2,
    Z1,
    add as py_ecc_add,
    multiply as py_ecc_mul,
    neg as py_ecc_neg,
    pairing as py_ecc_pairing,
    final_exponentiate as py_ecc_final_exponentiate,
    FQ12 as py_ecc_GT
)
from py_ecc.bls.g2_primitives import (  # noqa: F401
    G1_to_pubkey as py_ecc_G1_to_bytes48,
    pubkey_to_G1 as py_ecc_bytes48_to_G1,
    G2_to_signature as py_ecc_G2_to_bytes96,
    signature_to_G2 as py_ecc_bytes96_to_G2,
)


def pairing_check(values):
    p_q_1, p_q_2 = values
    final_exponentiation = py_ecc_final_exponentiate(
        py_ecc_pairing(p_q_1[1], p_q_1[0], final_exponentiate=False)
        * py_ecc_pairing(p_q_2[1], p_q_2[0], final_exponentiate=False)
    )
    return final_exponentiation == py_ecc_GT.one()


# Performs point addition of `lhs` and `rhs`
# The points can either be in G1 or G2
def add(lhs, rhs):
    return py_ecc_add(lhs, rhs)


# Performs Scalar multiplication between
# `point` and `scalar`
# `point` can either be in G1 or G2
def multiply(point, scalar):
    return py_ecc_mul(point, scalar)


# Returns the point negation of `point`
# `point` can either be in G1 or G2
def neg(point):
    return py_ecc_neg(point)


# Serializes a point in G1
# Returns a bytearray of size 48 as
# we use the compressed format
def G1_to_bytes48(point):
    return py_ecc_G1_to_bytes48(point)


# Serializes a point in G2
# Returns a bytearray of size 96 as
# we use the compressed format
def G2_to_bytes96(point):
    return py_ecc_G2_to_bytes96(point)


# Deserializes a purported compressed serialized
# point in G1
# - No subgroup checks are performed
# - If the bytearray is not a valid serialization
# of a point in G1, then this method will raise
# an exception
def bytes48_to_G1(bytes48):
    return py_ecc_bytes48_to_G1(bytes48)


# Deserializes a purported compressed serialized
# point in G2
# - No subgroup checks are performed
# - If the bytearray is not a valid serialization
# of a point in G2, then this method will raise
# an exception
def bytes96_to_G2(bytes96):
    return py_ecc_bytes96_to_G2(bytes96)



