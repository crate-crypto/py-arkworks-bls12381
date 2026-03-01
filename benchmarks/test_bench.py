"""Benchmarks for BLS12-381 operations using pytest-benchmark."""

import pytest
from py_arkworks_bls12381 import G1Point, G2Point, Scalar, GT


# --- Fixtures ---

@pytest.fixture
def g1():
    return G1Point()


@pytest.fixture
def g2():
    return G2Point()


@pytest.fixture
def g1_mult():
    return G1Point() * Scalar(123456789)


@pytest.fixture
def g2_mult():
    return G2Point() * Scalar(123456789)


# --- G1 benchmarks ---

def test_g1_add(benchmark, g1):
    benchmark(lambda: g1 + g1)


def test_g1_scalar_mul(benchmark, g1):
    s = Scalar(12345678910)
    benchmark(lambda: g1 * s)


def test_g1_to_compressed(benchmark, g1):
    benchmark(g1.to_compressed_bytes)


def test_g1_from_compressed(benchmark, g1):
    data = g1.to_compressed_bytes()
    benchmark(G1Point.from_compressed_bytes, data)


def test_g1_to_xy_bytes_be(benchmark, g1):
    benchmark(g1.to_xy_bytes_be)


def test_g1_from_xy_bytes_be(benchmark, g1):
    data = g1.to_xy_bytes_be()
    benchmark(G1Point.from_xy_bytes_be, data)


# --- G2 benchmarks ---

def test_g2_add(benchmark, g2):
    benchmark(lambda: g2 + g2)


def test_g2_scalar_mul(benchmark, g2):
    s = Scalar(12345678910)
    benchmark(lambda: g2 * s)


def test_g2_to_compressed(benchmark, g2):
    benchmark(g2.to_compressed_bytes)


def test_g2_from_compressed(benchmark, g2):
    data = g2.to_compressed_bytes()
    benchmark(G2Point.from_compressed_bytes, data)


def test_g2_to_xy_bytes_be(benchmark, g2):
    benchmark(g2.to_xy_bytes_be)


def test_g2_from_xy_bytes_be(benchmark, g2):
    data = g2.to_xy_bytes_be()
    benchmark(G2Point.from_xy_bytes_be, data)


# --- Pairing benchmarks ---

def test_pairing(benchmark, g1, g2):
    benchmark(GT.pairing, g1, g2)


def test_pairing_check_two_pairs(benchmark, g1, g2):
    neg_g1 = -g1
    benchmark(GT.pairing_check, [g1, neg_g1], [g2, g2])


def test_multi_pairing(benchmark, g1_mult, g2_mult, g1, g2):
    benchmark(GT.multi_pairing, [g1, g1_mult], [g2, g2_mult])


# --- Map to curve benchmarks ---

def test_map_fp_to_g1(benchmark):
    fp = bytes(47) + bytes([1])
    benchmark(G1Point.map_from_fp_be, fp)


def test_map_fp2_to_g2(benchmark):
    fp2 = bytes(47) + bytes([1]) + bytes(47) + bytes([2])
    benchmark(G2Point.map_from_fp2_be, fp2)


# --- MSM benchmarks ---

def test_g1_msm_10(benchmark, g1):
    points = [g1 * Scalar(i + 1) for i in range(10)]
    scalars = [Scalar(i + 100) for i in range(10)]
    benchmark(G1Point.multiexp_unchecked, points, scalars)


def test_g2_msm_10(benchmark, g2):
    points = [g2 * Scalar(i + 1) for i in range(10)]
    scalars = [Scalar(i + 100) for i in range(10)]
    benchmark(G2Point.multiexp_unchecked, points, scalars)
