import pytest
from py_arkworks_bls12381 import Scalar


class TestScalarArithmetic:
    def test_add(self):
        assert Scalar(2) + Scalar(3) == Scalar(5)

    def test_sub(self):
        assert Scalar(5) - Scalar(3) == Scalar(2)

    def test_mul(self):
        assert Scalar(3) * Scalar(4) == Scalar(12)

    def test_div(self):
        a = Scalar(6)
        b = Scalar(3)
        assert a / b == Scalar(2)

    def test_div_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            Scalar(1) / Scalar(0)

    def test_neg(self):
        a = Scalar(5)
        assert a + (-a) == Scalar(0)

    def test_pow(self):
        assert Scalar(2).pow(Scalar(10)) == Scalar(1024)

    def test_square(self):
        assert Scalar(5).square() == Scalar(25)


class TestScalarInverse:
    def test_inverse(self):
        a = Scalar(7)
        inv = a.inverse()
        assert a * inv == Scalar(1)

    def test_inverse_zero(self):
        with pytest.raises(ZeroDivisionError):
            Scalar(0).inverse()


class TestScalarPredicates:
    def test_is_zero(self):
        assert Scalar(0).is_zero()
        assert not Scalar(1).is_zero()

    def test_is_one(self):
        assert Scalar(1).is_one()
        assert not Scalar(0).is_one()


class TestScalarEquality:
    def test_eq(self):
        assert Scalar(42) == Scalar(42)

    def test_ne(self):
        assert Scalar(1) != Scalar(2)


class TestScalarConversion:
    def test_int(self):
        assert int(Scalar(42)) == 42

    def test_int_zero(self):
        assert int(Scalar(0)) == 0

    def test_int_large(self):
        val = 2**128 + 1
        assert int(Scalar(val)) == val


class TestScalarHash:
    def test_hashable(self):
        s = {Scalar(1), Scalar(2)}
        assert len(s) == 2

    def test_equal_scalars_same_hash(self):
        assert hash(Scalar(42)) == hash(Scalar(42))


class TestScalarRepr:
    def test_str(self):
        s = str(Scalar(42))
        assert len(s) > 0

    def test_repr(self):
        r = repr(Scalar(42))
        assert r.startswith("Scalar(")


class TestScalarLESerialization:
    def test_roundtrip(self):
        s = Scalar(42)
        data = s.to_le_bytes()
        assert len(data) == 32
        recovered = Scalar.from_le_bytes(data)
        assert s == recovered

    def test_zero_roundtrip(self):
        s = Scalar(0)
        data = s.to_le_bytes()
        assert data == bytes(32)
        assert Scalar.from_le_bytes(data) == s


class TestScalarBESerialization:
    def test_roundtrip(self):
        s = Scalar(42)
        data = s.to_be_bytes()
        assert len(data) == 32
        recovered = Scalar.from_be_bytes(data)
        assert s == recovered

    def test_last_byte(self):
        data = Scalar(42).to_be_bytes()
        assert data[-1] == 42
        assert all(b == 0 for b in data[:-1])

    def test_zero_roundtrip(self):
        s = Scalar(0)
        data = s.to_be_bytes()
        assert data == bytes(32)
        assert Scalar.from_be_bytes(data) == s

    def test_non_canonical_rejected(self):
        all_ones = bytes([0xFF] * 32)
        with pytest.raises(ValueError):
            Scalar.from_be_bytes(all_ones)

    def test_be_le_inverse(self):
        s = Scalar(42)
        be = s.to_be_bytes()
        le = s.to_le_bytes()
        assert be == bytes(reversed(le))


class TestScalarModOrder:
    def test_from_be_bytes_mod_order(self):
        all_ones = bytes([0xFF] * 32)
        s = Scalar.from_be_bytes_mod_order(all_ones)
        assert not s.is_zero()

    def test_from_le_bytes_mod_order(self):
        all_ones = bytes([0xFF] * 32)
        s = Scalar.from_le_bytes_mod_order(all_ones)
        assert not s.is_zero()

    def test_arbitrary_length(self):
        data = bytes([1, 2, 3])
        s = Scalar.from_be_bytes_mod_order(data)
        assert not s.is_zero()

    def test_canonical_value_unchanged(self):
        s = Scalar(42)
        data = s.to_be_bytes()
        recovered = Scalar.from_be_bytes_mod_order(data)
        assert s == recovered
