# py_arkworks_bls12381

The main usage of this library at this moment is to generate test vectors for EIP4844 in the [consensus-specs](https://github.com/ethereum/consensus-specs/tree/master). The library itself is generic, so feel free to use it for other purposes.

## G1/G2Points

```python
from py_arkworks_bls12381 import G1Point, G2Point, Scalar

# G1Point and G2Point have the same methods implemented on them
# For brevity, I will only show one method using G1Point and G2Point 
# The rest of the code will just use G1Point

# Point initialization -- This will be initialized to the g1 generator 
g1_generator = G1Point()
g2_generator = G2Point()

# Identity element 
identity = G1Point.identity()

# Equality -- We override eq and neq operators
assert g1_generator == g1_generator
assert g1_generator != identity


# Printing an element -- We override __str__ so when we print
# an element it prints in hex
print("identity: ",identity)
print("g1 generator: ", g1_generator)
print("g2 generator: ", g2_generator)

# Point Addition/subtraction/Negation -- We override the add/sub/neg operators
gen = G1Point()
double_gen = gen + gen
assert double_gen - gen == gen
neg_gen = -gen
assert neg_gen + gen == identity

# Scalar multiplication
#
scalar = Scalar(4)
four_gen = gen * scalar
assert four_gen == gen + gen + gen + gen

# Serialisation
# 
# serialising to/from a g1 point
# We don't expose the uncompressed form 
# because it seems like its not needed
compressed_bytes = gen.to_compressed_bytes()
deserialised_point = G1Point.from_compressed_bytes(compressed_bytes)
# If the bytes being received are trusted, we can avoid
# doing subgroup checks
deserialised_point_unchecked = G1Point.from_compressed_bytes_unchecked(compressed_bytes)
assert deserialised_point == deserialised_point_unchecked
assert deserialised_point == gen
```

## Pairing

```python
from py_arkworks_bls12381 import G1Point, G2Point, GT, Scalar


# Initilisation -- This is the generator point
gt_gen = GT()

# Zero/One
zero = GT.zero()
one = GT.one()

# Computing a pairing using pairing and multi_pairing
# multi_pairing does multiple pairings with only one final_exp
assert gt_gen == GT.pairing(G1Point(), G2Point()) 
g1s = [G1Point()]
g2s = [G2Point()]
assert gt_gen == GT.multi_pairing(g1s, g2s)

# Bilinearity
a = Scalar(1234)
b = Scalar(4566)
c = a * b


g = G1Point() * a
h = G2Point() * b

p = GT.pairing(g, h)

c_g1 = G1Point() *c
c_g2 = G2Point() *c

assert p == GT.pairing(c_g1, G2Point())
assert p == GT.pairing(G1Point(), c_g2)
```

## Scalar

```python
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
```

##  Development

You will need maturin to build the project.

```
pip install maturin
```


- First activate the virtual environment

```
 source .env/bin/activate
```

- Next build the rust package and install it in your virtual environment

```
maturin develop
```

- Now run a file in the examples folder

```
python3 examples/point.py
```

# Benchmarks

```
python3 -m examples.benches.bench
```
