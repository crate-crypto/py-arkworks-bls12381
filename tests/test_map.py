import pytest
from py_arkworks_bls12381 import G1Point, G2Point


class TestMapFromFpBE:
    def test_produces_valid_point(self):
        fp = bytes(47) + bytes([1])
        p = G1Point.map_from_fp_be(fp)
        raw = p.to_xy_bytes_be()
        recovered = G1Point.from_xy_bytes_be(raw)
        assert p == recovered

    def test_in_subgroup(self):
        fp = bytes(47) + bytes([1])
        p = G1Point.map_from_fp_be(fp)
        assert p.is_in_subgroup()

    def test_different_inputs_different_outputs(self):
        fp1 = bytes(47) + bytes([1])
        fp2 = bytes(47) + bytes([2])
        assert G1Point.map_from_fp_be(fp1) != G1Point.map_from_fp_be(fp2)

    def test_deterministic(self):
        fp = bytes(47) + bytes([42])
        assert G1Point.map_from_fp_be(fp) == G1Point.map_from_fp_be(fp)


class TestMapFromFpLE:
    def test_produces_valid_point(self):
        fp = bytes([1]) + bytes(47)
        p = G1Point.map_from_fp_le(fp)
        raw = p.to_xy_bytes_le()
        recovered = G1Point.from_xy_bytes_le(raw)
        assert p == recovered

    def test_in_subgroup(self):
        fp = bytes([1]) + bytes(47)
        p = G1Point.map_from_fp_le(fp)
        assert p.is_in_subgroup()

    def test_be_le_same_value(self):
        """Same field element via BE and LE should produce the same point."""
        fp_be = bytes(47) + bytes([1])
        fp_le = bytes([1]) + bytes(47)
        assert G1Point.map_from_fp_be(fp_be) == G1Point.map_from_fp_le(fp_le)


class TestMapFromFp2BE:
    def test_produces_valid_point(self):
        fp2 = bytes(47) + bytes([1]) + bytes(47) + bytes([2])
        p = G2Point.map_from_fp2_be(fp2)
        raw = p.to_xy_bytes_be()
        recovered = G2Point.from_xy_bytes_be(raw)
        assert p == recovered

    def test_in_subgroup(self):
        fp2 = bytes(47) + bytes([1]) + bytes(47) + bytes([2])
        p = G2Point.map_from_fp2_be(fp2)
        assert p.is_in_subgroup()

    def test_different_inputs_different_outputs(self):
        fp2_a = bytes(47) + bytes([1]) + bytes(47) + bytes([2])
        fp2_b = bytes(47) + bytes([3]) + bytes(47) + bytes([4])
        assert G2Point.map_from_fp2_be(fp2_a) != G2Point.map_from_fp2_be(fp2_b)

    def test_deterministic(self):
        fp2 = bytes(47) + bytes([1]) + bytes(47) + bytes([2])
        assert G2Point.map_from_fp2_be(fp2) == G2Point.map_from_fp2_be(fp2)


class TestMapFromFp2LE:
    def test_produces_valid_point(self):
        fp2 = bytes([1]) + bytes(47) + bytes([2]) + bytes(47)
        p = G2Point.map_from_fp2_le(fp2)
        raw = p.to_xy_bytes_le()
        recovered = G2Point.from_xy_bytes_le(raw)
        assert p == recovered

    def test_in_subgroup(self):
        fp2 = bytes([1]) + bytes(47) + bytes([2]) + bytes(47)
        p = G2Point.map_from_fp2_le(fp2)
        assert p.is_in_subgroup()

    def test_be_le_same_value(self):
        """Same Fp2 element via BE and LE should produce the same point."""
        fp2_be = bytes(47) + bytes([1]) + bytes(47) + bytes([2])
        fp2_le = bytes([1]) + bytes(47) + bytes([2]) + bytes(47)
        assert G2Point.map_from_fp2_be(fp2_be) == G2Point.map_from_fp2_le(fp2_le)
