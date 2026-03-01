import pytest
from py_arkworks_bls12381 import G2Point, Scalar


class TestG2Arithmetic:
    def test_addition(self, g2_gen, g2_identity):
        assert g2_gen + g2_identity == g2_gen

    def test_subtraction(self, g2_gen, g2_identity):
        assert g2_gen - g2_gen == g2_identity

    def test_negation(self, g2_gen, g2_identity):
        assert g2_gen + (-g2_gen) == g2_identity

    def test_scalar_mul(self, g2_gen):
        four_gen = g2_gen * Scalar(4)
        assert four_gen == g2_gen + g2_gen + g2_gen + g2_gen

    def test_double(self, g2_gen):
        double = g2_gen + g2_gen
        assert double == g2_gen * Scalar(2)


class TestG2Equality:
    def test_eq(self, g2_gen):
        assert g2_gen == g2_gen

    def test_ne(self, g2_gen, g2_identity):
        assert g2_gen != g2_identity

    def test_identity_eq(self, g2_identity):
        assert g2_identity == G2Point.identity()


class TestG2Hash:
    def test_hashable(self, g2_gen, g2_identity):
        s = {g2_gen, g2_identity}
        assert len(s) == 2

    def test_equal_points_same_hash(self, g2_gen):
        assert hash(g2_gen) == hash(G2Point())


class TestG2Repr:
    def test_str(self, g2_gen):
        s = str(g2_gen)
        assert len(s) > 0

    def test_repr(self, g2_gen):
        r = repr(g2_gen)
        assert r.startswith("G2Point(0x")


class TestG2Subgroup:
    def test_generator_in_subgroup(self, g2_gen):
        assert g2_gen.is_in_subgroup()

    def test_identity_in_subgroup(self, g2_identity):
        assert g2_identity.is_in_subgroup()


class TestG2CompressedSerialization:
    def test_roundtrip(self, g2_gen):
        data = g2_gen.to_compressed_bytes()
        assert len(data) == 96
        recovered = G2Point.from_compressed_bytes(data)
        assert g2_gen == recovered

    def test_roundtrip_unchecked(self, g2_gen):
        data = g2_gen.to_compressed_bytes()
        recovered = G2Point.from_compressed_bytes_unchecked(data)
        assert g2_gen == recovered

    def test_identity_roundtrip(self, g2_identity):
        data = g2_identity.to_compressed_bytes()
        recovered = G2Point.from_compressed_bytes(data)
        assert g2_identity == recovered


class TestG2UncompressedBE:
    def test_roundtrip(self, g2_gen):
        data = g2_gen.to_xy_bytes_be()
        assert len(data) == 192
        recovered = G2Point.from_xy_bytes_be(data)
        assert g2_gen == recovered

    def test_roundtrip_unchecked(self, g2_gen):
        data = g2_gen.to_xy_bytes_be()
        recovered = G2Point.from_xy_bytes_unchecked_be(data)
        assert g2_gen == recovered

    def test_identity(self, g2_identity):
        data = g2_identity.to_xy_bytes_be()
        assert data == bytes(192)
        recovered = G2Point.from_xy_bytes_be(data)
        assert g2_identity == recovered

    def test_arithmetic_roundtrip(self, g2_gen):
        p = g2_gen + g2_gen * Scalar(5)
        data = p.to_xy_bytes_be()
        recovered = G2Point.from_xy_bytes_be(data)
        assert p == recovered

    def test_invalid_point_rejected(self):
        bad = bytes([0xFF] * 192)
        with pytest.raises(ValueError):
            G2Point.from_xy_bytes_be(bad)


class TestG2UncompressedLE:
    def test_roundtrip(self, g2_gen):
        data = g2_gen.to_xy_bytes_le()
        assert len(data) == 192
        recovered = G2Point.from_xy_bytes_le(data)
        assert g2_gen == recovered

    def test_roundtrip_unchecked(self, g2_gen):
        data = g2_gen.to_xy_bytes_le()
        recovered = G2Point.from_xy_bytes_unchecked_le(data)
        assert g2_gen == recovered

    def test_identity(self, g2_identity):
        data = g2_identity.to_xy_bytes_le()
        assert data == bytes(192)
        recovered = G2Point.from_xy_bytes_le(data)
        assert g2_identity == recovered

    def test_be_le_differ(self, g2_gen):
        be = g2_gen.to_xy_bytes_be()
        le = g2_gen.to_xy_bytes_le()
        assert be != le


class TestG2MSM:
    def test_msm_basic(self, g2_gen):
        points = [g2_gen, g2_gen]
        scalars = [Scalar(2), Scalar(3)]
        result = G2Point.multiexp_unchecked(points, scalars)
        expected = g2_gen * Scalar(5)
        assert result == expected

    def test_msm_single(self, g2_gen):
        result = G2Point.multiexp_unchecked([g2_gen], [Scalar(7)])
        assert result == g2_gen * Scalar(7)
