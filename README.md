# py_arkworks_bls12381

Python bindings for BLS12-381 curve operations using [arkworks](https://github.com/arkworks-rs/algebra). Built with [PyO3](https://pyo3.rs/) and [maturin](https://www.maturin.rs/).

The main usage of this library at this moment is to generate test vectors for EIP4844 in the [consensus-specs](https://github.com/ethereum/consensus-specs/tree/master). The library itself is generic, so feel free to use it for other purposes.

Requires Python >= 3.11.

## G1/G2 Points

```python
from py_arkworks_bls12381 import G1Point, G2Point, Scalar

# G1Point and G2Point have the same methods implemented on them.
# For brevity, most examples below use G1Point only.

# Point initialization -- defaults to the generator
g1_generator = G1Point()
g2_generator = G2Point()

# Identity element
identity = G1Point.identity()

# Equality
assert g1_generator == g1_generator
assert g1_generator != identity

# Printing -- __str__ returns hex
print("identity: ", identity)
print("g1 generator: ", g1_generator)
print("g2 generator: ", g2_generator)

# Arithmetic -- add/sub/neg/scalar mul
gen = G1Point()
double_gen = gen + gen
assert double_gen - gen == gen
neg_gen = -gen
assert neg_gen + gen == identity

scalar = Scalar(4)
four_gen = gen * scalar
assert four_gen == gen + gen + gen + gen

# Subgroup check
assert gen.is_in_subgroup()

# Multi-scalar multiplication
result = G1Point.multiexp_unchecked([gen, gen], [Scalar(2), Scalar(3)])
assert result == gen * Scalar(5)
```

## Serialization

```python
from py_arkworks_bls12381 import G1Point, G2Point, Scalar

gen = G1Point()

# Compressed (48 bytes for G1, 96 bytes for G2)
compressed = gen.to_compressed_bytes()
assert gen == G1Point.from_compressed_bytes(compressed)
# Skip subgroup check for trusted bytes:
assert gen == G1Point.from_compressed_bytes_unchecked(compressed)

# Uncompressed xy coordinates (96 bytes for G1, 192 bytes for G2)
# Explicit endianness: _be for big-endian, _le for little-endian
xy_be = gen.to_xy_bytes_be()
assert gen == G1Point.from_xy_bytes_be(xy_be)

xy_le = gen.to_xy_bytes_le()
assert gen == G1Point.from_xy_bytes_le(xy_le)

# Unchecked variants (skip subgroup check, still checks on-curve)
assert gen == G1Point.from_xy_bytes_unchecked_be(xy_be)
assert gen == G1Point.from_xy_bytes_unchecked_le(xy_le)

# Scalar serialization -- big-endian and little-endian
s = Scalar(42)
assert s == Scalar.from_le_bytes(s.to_le_bytes())
assert s == Scalar.from_be_bytes(s.to_be_bytes())
```

## Map to Curve

```python
from py_arkworks_bls12381 import G1Point, G2Point

# Map an Fp element (48 bytes) to G1 using SWU map + cofactor clearing
fp_bytes = bytes(47) + bytes([1])
g1 = G1Point.map_from_fp_be(fp_bytes)   # big-endian input
g1 = G1Point.map_from_fp_le(fp_bytes)   # little-endian input

# Map an Fp2 element (96 bytes: c0 || c1) to G2
fp2_bytes = bytes(47) + bytes([1]) + bytes(47) + bytes([2])
g2 = G2Point.map_from_fp2_be(fp2_bytes)
g2 = G2Point.map_from_fp2_le(fp2_bytes)
```

## Pairing

```python
from py_arkworks_bls12381 import G1Point, G2Point, GT, Scalar

# Generator pairing
gt_gen = GT()
assert gt_gen == GT.pairing(G1Point(), G2Point())

# Multi-pairing (single final exponentiation)
g1s = [G1Point()]
g2s = [G2Point()]
assert gt_gen == GT.multi_pairing(g1s, g2s)

# Pairing check: returns True if product of pairings equals identity
# e(G1, G2) * e(-G1, G2) == 1
g1 = G1Point()
g2 = G2Point()
assert GT.pairing_check([g1, -g1], [g2, g2])
assert not GT.pairing_check([g1], [g2])

# Bilinearity
a = Scalar(1234)
b = Scalar(4566)
c = a * b

g = G1Point() * a
h = G2Point() * b
p = GT.pairing(g, h)

assert p == GT.pairing(G1Point() * c, G2Point())
assert p == GT.pairing(G1Point(), G2Point() * c)
```

## Scalar

```python
from py_arkworks_bls12381 import Scalar

scalar = Scalar(12345)

# Equality
assert scalar == scalar
assert Scalar(1234) != Scalar(4567)

# Arithmetic
a = Scalar(3)
b = Scalar(4)
c = Scalar(5)
assert a.square() + b.square() == c.square()
assert a * a + b * b == c * c

neg_a = -a
assert a + neg_a == Scalar(0)
assert (a + neg_a).is_zero()

# Division, pow, inverse
assert a / a == Scalar(1)
assert a.pow(Scalar(2)) == a.square()
assert a * a.inverse() == Scalar(1)

# Convert to/from int
assert int(Scalar(42)) == 42
```

## Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/):

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Set up the development environment:

```
uv venv
uv pip install maturin
uv pip install -e ".[dev]"
uv run maturin develop
```

Run the tests:

```
uv run pytest
```
