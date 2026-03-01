"""
Example demonstrating BLS12-381 operations needed for EIP-2537 precompiles.

Covers: G1/G2 uncompressed serialization, big-endian scalars,
        map-to-curve (MAP_FP_TO_G1, MAP_FP2_TO_G2), and pairing check.

The library uses raw 48-byte big-endian field elements.
EIP-2537 callers would add/remove 16-byte zero-padding per field element themselves.
"""

from py_arkworks_bls12381 import G1Point, G2Point, Scalar, GT

# --- 1. G1 raw bytes (uncompressed, big-endian) ---
print("=== G1 Raw Bytes (96-byte uncompressed format) ===")

g1_gen = G1Point()
raw = g1_gen.to_xy_bytes_be()
assert len(raw) == 96, f"Expected 96 bytes, got {len(raw)}"
print(f"G1 generator raw bytes length: {len(raw)}")

# Roundtrip
g1_recovered = G1Point.from_xy_bytes_be(raw)
assert g1_gen == g1_recovered, "G1 roundtrip failed"
print("G1 generator roundtrip: OK")

# Unchecked variant
g1_unchecked = G1Point.from_xy_bytes_unchecked_be(raw)
assert g1_gen == g1_unchecked, "G1 unchecked roundtrip failed"
print("G1 generator unchecked roundtrip: OK")

# Identity (point at infinity) = all zeros
g1_inf = G1Point.identity()
inf_raw = g1_inf.to_xy_bytes_be()
assert inf_raw == bytes(96), "Identity should be 96 zero bytes"
g1_inf_recovered = G1Point.from_xy_bytes_be(inf_raw)
assert g1_inf == g1_inf_recovered, "Identity roundtrip failed"
print("G1 identity (point at infinity) roundtrip: OK")

# --- 2. G2 raw bytes (uncompressed, big-endian) ---
print("\n=== G2 Raw Bytes (192-byte uncompressed format) ===")

g2_gen = G2Point()
raw2 = g2_gen.to_xy_bytes_be()
assert len(raw2) == 192, f"Expected 192 bytes, got {len(raw2)}"
print(f"G2 generator raw bytes length: {len(raw2)}")

g2_recovered = G2Point.from_xy_bytes_be(raw2)
assert g2_gen == g2_recovered, "G2 roundtrip failed"
print("G2 generator roundtrip: OK")

g2_unchecked = G2Point.from_xy_bytes_unchecked_be(raw2)
assert g2_gen == g2_unchecked, "G2 unchecked roundtrip failed"
print("G2 generator unchecked roundtrip: OK")

g2_inf = G2Point.identity()
inf_raw2 = g2_inf.to_xy_bytes_be()
assert inf_raw2 == bytes(192), "G2 identity should be 192 zero bytes"
g2_inf_recovered = G2Point.from_xy_bytes_be(inf_raw2)
assert g2_inf == g2_inf_recovered, "G2 identity roundtrip failed"
print("G2 identity (point at infinity) roundtrip: OK")

# --- 3. Scalar big-endian ---
print("\n=== Scalar Big-Endian (32-byte) ===")

s = Scalar(42)
be_bytes = s.to_be_bytes()
assert len(be_bytes) == 32, f"Expected 32 bytes, got {len(be_bytes)}"
# 42 in big-endian should have 0x2a as the last byte
assert be_bytes[-1] == 42, f"Expected last byte = 42, got {be_bytes[-1]}"
assert all(b == 0 for b in be_bytes[:-1]), "Leading bytes should be zero"
print(f"Scalar(42) to_be_bytes: OK")

s_recovered = Scalar.from_be_bytes(be_bytes)
assert s == s_recovered, "Scalar big-endian roundtrip failed"
print("Scalar big-endian roundtrip: OK")

# Non-canonical scalars (>= subgroup order) are rejected
all_ones = bytes([0xff] * 32)
try:
    Scalar.from_be_bytes(all_ones)
    assert False, "Should have raised ValueError"
except ValueError:
    print("Scalar from 0xff*32: correctly rejected (non-canonical): OK")

# --- 4. MAP_FP_TO_G1 ---
print("\n=== MAP_FP_TO_G1 ===")

# Create a valid Fp element (48-byte big-endian)
# Use a simple value: 1
fp_bytes = bytes(47) + bytes([1])  # 48 bytes, value = 1
g1_mapped = G1Point.map_from_fp_be(fp_bytes)
# Verify it's a valid point by roundtripping through raw bytes
mapped_raw = g1_mapped.to_xy_bytes_be()
g1_check = G1Point.from_xy_bytes_be(mapped_raw)
assert g1_mapped == g1_check, "map_from_fp_be result is not a valid G1 point"
print("map_from_fp_be(1): OK - produces valid G1 point in subgroup")

# Different input produces different output
fp_bytes_2 = bytes(47) + bytes([2])
g1_mapped_2 = G1Point.map_from_fp_be(fp_bytes_2)
assert g1_mapped != g1_mapped_2, "Different Fp should produce different G1 points"
print("map_from_fp_be(1) != map_from_fp_be(2): OK")

# --- 5. MAP_FP2_TO_G2 ---
print("\n=== MAP_FP2_TO_G2 ===")

# Create a valid Fp2 element (96 bytes = c0: 48B || c1: 48B)
fp2_bytes = bytes(47) + bytes([1]) + bytes(47) + bytes([2])  # c0=1, c1=2
g2_mapped = G2Point.map_from_fp2_be(fp2_bytes)
mapped_raw2 = g2_mapped.to_xy_bytes_be()
g2_check = G2Point.from_xy_bytes_be(mapped_raw2)
assert g2_mapped == g2_check, "map_from_fp2_be result is not a valid G2 point"
print("map_from_fp2_be(1, 2): OK - produces valid G2 point in subgroup")

# --- 6. Pairing Check ---
print("\n=== Pairing Check ===")

# e(G1, G2) * e(-G1, G2) should equal identity
g1 = G1Point()
g2 = G2Point()
neg_g1 = -g1

result = GT.pairing_check([g1, neg_g1], [g2, g2])
assert result is True, "Pairing check should pass: e(G1,G2)*e(-G1,G2) == 1"
print("pairing_check([G1, -G1], [G2, G2]) = True: OK")

# e(G1, G2) alone should NOT equal identity
result2 = GT.pairing_check([g1], [g2])
assert result2 is False, "Single pairing should not equal identity"
print("pairing_check([G1], [G2]) = False: OK")

# Empty input should return True
result3 = GT.pairing_check([], [])
assert result3 is True, "Empty pairing check should return True"
print("pairing_check([], []) = True: OK")

# e(2*G1, G2) * e(G1, -2*G2) should equal identity (bilinearity)
s2 = Scalar(2)
g1_2 = g1 * s2
neg_g2_2 = -(g2 * s2)
result4 = GT.pairing_check([g1_2, g1], [g2, neg_g2_2])
assert result4 is True, "Bilinearity check failed"
print("pairing_check([2*G1, G1], [G2, -2*G2]) = True: OK (bilinearity)")

# Mismatched lengths should raise ValueError
try:
    GT.pairing_check([g1], [g2, g2])
    assert False, "Should have raised ValueError"
except ValueError:
    print("pairing_check with mismatched lengths: raises ValueError: OK")

# --- 7. Arithmetic with raw bytes ---
print("\n=== Arithmetic with raw bytes serialization ===")

# G1: a + b serialized via raw bytes
a = G1Point()
b = G1Point() * Scalar(3)
c = a + b  # 4*G1
c_raw = c.to_xy_bytes_be()
c_from_raw = G1Point.from_xy_bytes_be(c_raw)
assert c == c_from_raw, "G1 addition result roundtrip failed"
print("G1 addition + raw bytes roundtrip: OK")

# G2 same test
a2 = G2Point()
b2 = G2Point() * Scalar(5)
c2 = a2 + b2
c2_raw = c2.to_xy_bytes_be()
c2_from_raw = G2Point.from_xy_bytes_be(c2_raw)
assert c2 == c2_from_raw, "G2 addition result roundtrip failed"
print("G2 addition + raw bytes roundtrip: OK")

print("\n=== All tests passed! ===")
