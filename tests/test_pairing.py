import pytest
from py_arkworks_bls12381 import G1Point, G2Point, Scalar, GT


class TestPairing:
    def test_bilinearity(self, g1_gen, g2_gen):
        """e(a*G1, G2) == e(G1, a*G2)"""
        a = Scalar(5)
        lhs = GT.pairing(g1_gen * a, g2_gen)
        rhs = GT.pairing(g1_gen, g2_gen * a)
        assert lhs == rhs

    def test_non_degeneracy(self, g1_gen, g2_gen):
        result = GT.pairing(g1_gen, g2_gen)
        assert result != GT.one()

    def test_identity_g1(self, g1_identity, g2_gen):
        result = GT.pairing(g1_identity, g2_gen)
        assert result == GT.one()

    def test_identity_g2(self, g1_gen, g2_identity):
        result = GT.pairing(g1_gen, g2_identity)
        assert result == GT.one()


class TestMultiPairing:
    def test_basic(self, g1_gen, g2_gen):
        result = GT.multi_pairing([g1_gen], [g2_gen])
        single = GT.pairing(g1_gen, g2_gen)
        assert result == single

    def test_product(self, g1_gen, g2_gen):
        """multi_pairing([P1,P2], [Q1,Q2]) == e(P1,Q1) * e(P2,Q2)"""
        p1 = g1_gen * Scalar(2)
        p2 = g1_gen * Scalar(3)
        q1 = g2_gen
        q2 = g2_gen * Scalar(4)
        multi = GT.multi_pairing([p1, p2], [q1, q2])
        separate = GT.pairing(p1, q1) * GT.pairing(p2, q2)
        assert multi == separate

    def test_mismatched_lengths(self, g1_gen, g2_gen):
        with pytest.raises(ValueError):
            GT.multi_pairing([g1_gen], [g2_gen, g2_gen])


class TestPairingCheck:
    def test_cancellation(self, g1_gen, g2_gen):
        """e(G1, G2) * e(-G1, G2) == 1"""
        assert GT.pairing_check([g1_gen, -g1_gen], [g2_gen, g2_gen])

    def test_single_non_identity(self, g1_gen, g2_gen):
        assert not GT.pairing_check([g1_gen], [g2_gen])

    def test_empty(self):
        assert GT.pairing_check([], [])

    def test_bilinearity(self, g1_gen, g2_gen):
        """e(2*G1, G2) * e(G1, -2*G2) == 1"""
        s2 = Scalar(2)
        g1_2 = g1_gen * s2
        neg_g2_2 = -(g2_gen * s2)
        assert GT.pairing_check([g1_2, g1_gen], [g2_gen, neg_g2_2])

    def test_mismatched_lengths(self, g1_gen, g2_gen):
        with pytest.raises(ValueError):
            GT.pairing_check([g1_gen], [g2_gen, g2_gen])


class TestGTArithmetic:
    def test_generator(self):
        g = GT()
        assert g != GT.one()

    def test_one(self):
        assert GT.one() != GT.zero()

    def test_mul(self, g1_gen, g2_gen):
        e = GT.pairing(g1_gen, g2_gen)
        assert e * GT.one() == e


class TestGTRepr:
    def test_str(self):
        s = str(GT.one())
        assert len(s) > 0

    def test_repr(self):
        r = repr(GT.one())
        assert r.startswith("GT(0x")

    def test_hash(self):
        s = {GT.one(), GT.zero()}
        assert len(s) == 2
