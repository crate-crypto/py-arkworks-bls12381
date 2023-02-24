from py_arkworks_bls12381 import Scalar

# Initialisation - The default initialiser for a scalar is an u128 integer
scalar = Scalar(12345)

# Equality -- We override eq and neq operators
assert scalar == scalar
assert Scalar(1234) != Scalar(4567)

# Scalar Addition/subtraction/Negation -- We override the add/sub/neg operators
a = Scalar(3)
b = Scalar(4)
c = Scalar(5)
assert a.square() + b.square() == c.square()
assert a * a + b * b == c * c

neg_a = -a
assert a + neg_a == Scalar(0)
assert (a + neg_a).is_zero()

# Serialisation
compressed_bytes = scalar.to_le_bytes()
deserialised_scalar = Scalar.from_le_bytes(compressed_bytes)
assert scalar == deserialised_scalar