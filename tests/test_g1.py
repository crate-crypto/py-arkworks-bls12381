import pytest
from py_arkworks_bls12381 import G1Point, Scalar


class TestG1Arithmetic:
    def test_addition(self, g1_gen, g1_identity):
        assert g1_gen + g1_identity == g1_gen

    def test_subtraction(self, g1_gen, g1_identity):
        assert g1_gen - g1_gen == g1_identity

    def test_negation(self, g1_gen, g1_identity):
        assert g1_gen + (-g1_gen) == g1_identity

    def test_scalar_mul(self, g1_gen):
        four_gen = g1_gen * Scalar(4)
        assert four_gen == g1_gen + g1_gen + g1_gen + g1_gen

    def test_double(self, g1_gen):
        double = g1_gen + g1_gen
        assert double == g1_gen * Scalar(2)


class TestG1Equality:
    def test_eq(self, g1_gen):
        assert g1_gen == g1_gen

    def test_ne(self, g1_gen, g1_identity):
        assert g1_gen != g1_identity

    def test_identity_eq(self, g1_identity):
        assert g1_identity == G1Point.identity()


class TestG1Hash:
    def test_hashable(self, g1_gen, g1_identity):
        s = {g1_gen, g1_identity}
        assert len(s) == 2

    def test_equal_points_same_hash(self, g1_gen):
        assert hash(g1_gen) == hash(G1Point())


class TestG1Repr:
    def test_str(self, g1_gen):
        s = str(g1_gen)
        assert len(s) > 0

    def test_repr(self, g1_gen):
        r = repr(g1_gen)
        assert r.startswith("G1Point(0x")


class TestG1Subgroup:
    def test_generator_in_subgroup(self, g1_gen):
        assert g1_gen.is_in_subgroup()

    def test_identity_in_subgroup(self, g1_identity):
        assert g1_identity.is_in_subgroup()


class TestG1CompressedSerialization:
    def test_roundtrip(self, g1_gen):
        data = g1_gen.to_compressed_bytes()
        assert len(data) == 48
        recovered = G1Point.from_compressed_bytes(data)
        assert g1_gen == recovered

    def test_roundtrip_unchecked(self, g1_gen):
        data = g1_gen.to_compressed_bytes()
        recovered = G1Point.from_compressed_bytes_unchecked(data)
        assert g1_gen == recovered

    def test_identity_roundtrip(self, g1_identity):
        data = g1_identity.to_compressed_bytes()
        recovered = G1Point.from_compressed_bytes(data)
        assert g1_identity == recovered


class TestG1UncompressedBE:
    def test_roundtrip(self, g1_gen):
        data = g1_gen.to_xy_bytes_be()
        assert len(data) == 96
        recovered = G1Point.from_xy_bytes_be(data)
        assert g1_gen == recovered

    def test_roundtrip_unchecked(self, g1_gen):
        data = g1_gen.to_xy_bytes_be()
        recovered = G1Point.from_xy_bytes_unchecked_be(data)
        assert g1_gen == recovered

    def test_identity(self, g1_identity):
        data = g1_identity.to_xy_bytes_be()
        assert data == bytes(96)
        recovered = G1Point.from_xy_bytes_be(data)
        assert g1_identity == recovered

    def test_arithmetic_roundtrip(self, g1_gen):
        p = g1_gen + g1_gen * Scalar(3)
        data = p.to_xy_bytes_be()
        recovered = G1Point.from_xy_bytes_be(data)
        assert p == recovered

    def test_invalid_point_rejected(self):
        bad = bytes([0xFF] * 96)
        with pytest.raises(ValueError):
            G1Point.from_xy_bytes_be(bad)


class TestG1UncompressedLE:
    def test_roundtrip(self, g1_gen):
        data = g1_gen.to_xy_bytes_le()
        assert len(data) == 96
        recovered = G1Point.from_xy_bytes_le(data)
        assert g1_gen == recovered

    def test_roundtrip_unchecked(self, g1_gen):
        data = g1_gen.to_xy_bytes_le()
        recovered = G1Point.from_xy_bytes_unchecked_le(data)
        assert g1_gen == recovered

    def test_identity(self, g1_identity):
        data = g1_identity.to_xy_bytes_le()
        assert data == bytes(96)
        recovered = G1Point.from_xy_bytes_le(data)
        assert g1_identity == recovered

    def test_be_le_differ(self, g1_gen):
        be = g1_gen.to_xy_bytes_be()
        le = g1_gen.to_xy_bytes_le()
        assert be != le


class TestG1MSM:
    def test_msm_basic(self, g1_gen):
        points = [g1_gen, g1_gen]
        scalars = [Scalar(2), Scalar(3)]
        result = G1Point.multiexp_unchecked(points, scalars)
        expected = g1_gen * Scalar(5)
        assert result == expected

    def test_msm_single(self, g1_gen):
        result = G1Point.multiexp_unchecked([g1_gen], [Scalar(7)])
        assert result == g1_gen * Scalar(7)
