import pytest
from py_arkworks_bls12381 import G1Point, G2Point, Scalar, GT


@pytest.fixture
def g1_gen():
    return G1Point()


@pytest.fixture
def g2_gen():
    return G2Point()


@pytest.fixture
def g1_identity():
    return G1Point.identity()


@pytest.fixture
def g2_identity():
    return G2Point.identity()
