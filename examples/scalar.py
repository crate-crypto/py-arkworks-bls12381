from py_arkworks_bls12381 import Scalar

BLS_MODULUS = 52435875175126190479447740508185965837690552500527637822603658699938581184513

# Initialisation - The default initialiser for a scalar is an u128 integer
scalar = Scalar(12345)

# It should be possible to instantiate BLS_MODULUS - 1
max_value = Scalar(BLS_MODULUS - 1)
assert max_value + Scalar(2) == Scalar(1)

# Equality -- We override eq and neq operators
assert scalar == scalar
assert Scalar(1234) != Scalar(4567)

# Scalar arithmetic -- We override the mul/div/add/sub/neg operators
a = Scalar(3)
b = Scalar(4)
c = Scalar(5)
assert a.square() + b.square() == c.square()
assert a * a + b * b == c * c

assert Scalar(12) / Scalar(3) == Scalar(4)

try:
    assert Scalar(12) / Scalar(0)
    assert False
except ZeroDivisionError:
    pass

exp = Scalar(0xffff_ffff_ffff_fff)
assert int(Scalar(2).pow(exp)) == pow(2, int(exp), BLS_MODULUS)

neg_a = -a
assert a + neg_a == Scalar(0)
assert (a + neg_a).is_zero()

# Serialisation
compressed_bytes = scalar.to_le_bytes()
deserialised_scalar = Scalar.from_le_bytes(compressed_bytes)
assert scalar == deserialised_scalar

# Conversion to int
assert int(Scalar(0)) == 0
assert int(Scalar(12345)) == 12345