"""
BLS signature verification implemented on top of py-arkworks, cross-checked
against py-ecc.

This is the Ethereum BLS scheme (minimal-pubkey-size): public keys live in G1,
signatures in G2, using ciphersuite ``BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_``.

Everything here is built from the bindings py-arkworks exposes:

  * ``G2Point.hash_to_curve``   (full RFC 9380 hash-to-curve, message -> G2)
  * ``GT.pairing_check``        (the pairing equation)
  * ``*.from_compressed_bytes`` (point deserialization, with subgroup checks)

The only pure-Python logic is ``verify`` itself, which wires the three together.
"""

import pytest
from py_arkworks_bls12381 import G1Point, G2Point, GT, Scalar

from py_ecc.bls import G2ProofOfPossession as PyEccBLS


# Ciphersuite domain separation tag for signatures in G2.
DST = PyEccBLS.DST

FP_SIZE = 48


def verify(pubkey: bytes, msg: bytes, signature: bytes) -> bool:
    """Verify a BLS signature using py-arkworks primitives.

    Checks ``e(G1, sig) * e(-PK, H(m)) == 1``.
    """
    try:
        pk = G1Point.from_compressed_bytes(pubkey)
        sig = G2Point.from_compressed_bytes(signature)
    except ValueError:
        return False
    h_m = G2Point.hash_to_curve(msg, DST)
    g1_gen = G1Point()
    return GT.pairing_check([g1_gen, -pk], [sig, h_m])


def sk_to_pk(sk: int) -> bytes:
    """Derive a public key with py-arkworks primitives (PK = sk * G1)."""
    return (G1Point() * Scalar(sk)).to_compressed_bytes()


def sign(sk: int, msg: bytes) -> bytes:
    """Sign a message with py-arkworks primitives (sig = sk * H(m))."""
    return (G2Point.hash_to_curve(msg, DST) * Scalar(sk)).to_compressed_bytes()


# py-ecc is the reference implementation; we use it to mint the keys and
# signatures that our verify() is then checked against.
MESSAGES = [b"", b"hello world", b"\x00", bytes(range(32)), b"a" * 100]


def _keypair(seed: int):
    sk = PyEccBLS.KeyGen(seed.to_bytes(32, "big"))
    pk = PyEccBLS.SkToPk(sk)
    return sk, pk


@pytest.fixture(params=range(len(MESSAGES)))
def signed(request):
    msg = MESSAGES[request.param]
    sk, pk = _keypair(request.param + 1)
    sig = PyEccBLS.Sign(sk, msg)
    return pk, msg, sig


class TestHashToCurveMatchesPyEcc:
    """The native G2Point.hash_to_curve must equal py-ecc's hash_to_G2."""

    @pytest.mark.parametrize("msg", MESSAGES)
    def test_matches(self, msg):
        import hashlib

        from py_ecc.bls.hash_to_curve import hash_to_G2
        from py_ecc.bls.g2_primitives import G2_to_signature

        expected = G2Point.from_compressed_bytes(
            G2_to_signature(hash_to_G2(msg, DST, hashlib.sha256))
        )
        assert G2Point.hash_to_curve(msg, DST) == expected


class TestVerify:
    def test_valid_signature(self, signed):
        pk, msg, sig = signed
        assert verify(pk, msg, sig)

    def test_agrees_with_py_ecc_on_valid(self, signed):
        pk, msg, sig = signed
        assert verify(pk, msg, sig) == PyEccBLS.Verify(pk, msg, sig)

    def test_wrong_message_fails(self, signed):
        pk, msg, sig = signed
        tampered = msg + b"!"
        assert not verify(pk, tampered, sig)
        assert PyEccBLS.Verify(pk, tampered, sig) is False

    def test_wrong_pubkey_fails(self, signed):
        pk, msg, sig = signed
        _, other_pk = _keypair(999)
        assert not verify(other_pk, msg, sig)
        assert PyEccBLS.Verify(other_pk, msg, sig) is False

    def test_tampered_signature_fails(self, signed):
        pk, msg, sig = signed
        # A well-formed signature over the same message but from a different
        # key: it decodes cleanly, so this exercises the pairing check itself
        # rejecting it (not just deserialization failing).
        other_sk, _ = _keypair(12345)
        bad_sig = PyEccBLS.Sign(other_sk, msg)
        assert not verify(pk, msg, bad_sig)


class TestVerifyMalformedInputs:
    """Adversarial / malformed inputs must be rejected (return False, not raise),
    matching py-ecc."""

    @pytest.fixture
    def good_sig(self):
        sk, pk = _keypair(1)
        return pk, b"hello world", PyEccBLS.Sign(sk, b"hello world")

    def test_wrong_length_pubkey(self, good_sig):
        _, msg, sig = good_sig
        assert verify(b"\x00" * 10, msg, sig) is False
        assert PyEccBLS.Verify(b"\x00" * 10, msg, sig) is False

    def test_wrong_length_signature(self, good_sig):
        pk, msg, _ = good_sig
        assert verify(pk, msg, b"\x00" * 10) is False
        assert PyEccBLS.Verify(pk, msg, b"\x00" * 10) is False

    def test_garbage_pubkey(self, good_sig):
        # Right length, but not a valid compressed point encoding.
        _, msg, sig = good_sig
        assert verify(b"\x01" + b"\x00" * 47, msg, sig) is False
        assert PyEccBLS.Verify(b"\x01" + b"\x00" * 47, msg, sig) is False

    def test_garbage_signature(self, good_sig):
        pk, msg, _ = good_sig
        assert verify(pk, msg, b"\x01" + b"\x00" * 95) is False
        assert PyEccBLS.Verify(pk, msg, b"\x01" + b"\x00" * 95) is False

    def test_infinity_pubkey(self, good_sig):
        # Compressed point at infinity: high 3 bits = 0b110, rest zero.
        _, msg, sig = good_sig
        inf_pk = bytes([0xC0]) + b"\x00" * 47
        assert verify(inf_pk, msg, sig) is False
        assert PyEccBLS.Verify(inf_pk, msg, sig) is False

    def test_infinity_signature(self, good_sig):
        pk, msg, _ = good_sig
        inf_sig = bytes([0xC0]) + b"\x00" * 95
        assert verify(pk, msg, inf_sig) is False
        assert PyEccBLS.Verify(pk, msg, inf_sig) is False


# Official RFC 9380 hash-to-curve reference vectors for suite
# BLS12381G2_XMD:SHA-256_SSWU_RO_ (Appendix J.10.1). These come from the IETF
# spec, not from py-ecc, so they pin G2Point.hash_to_curve to an authority
# independent of the differential tests above.
#
# The DST is the RFC's own test DST, which differs from the BLS-signature DST.
# Each entry is (msg, P.x.c0, P.x.c1, P.y.c0, P.y.c1) as hex.
RFC9380_DST = b"QUUX-V01-CS02-with-BLS12381G2_XMD:SHA-256_SSWU_RO_"

RFC9380_VECTORS = [
    ("", "0x0141ebfbdca40eb85b87142e130ab689c673cf60f1a3e98d69335266f30d9b8d4ac44c1038e9dcdd5393faf5c41fb78a", "0x05cb8437535e20ecffaef7752baddf98034139c38452458baeefab379ba13dff5bf5dd71b72418717047f5b0f37da03d", "0x0503921d7f6a12805e72940b963c0cf3471c7b2a524950ca195d11062ee75ec076daf2d4bc358c4b190c0c98064fdd92", "0x12424ac32561493f3fe3c260708a12b7c620e7be00099a974e259ddc7d1f6395c3c811cdd19f1e8dbf3e9ecfdcbab8d6"),
    ("abc", "0x02c2d18e033b960562aae3cab37a27ce00d80ccd5ba4b7fe0e7a210245129dbec7780ccc7954725f4168aff2787776e6", "0x139cddbccdc5e91b9623efd38c49f81a6f83f175e80b06fc374de9eb4b41dfe4ca3a230ed250fbe3a2acf73a41177fd8", "0x1787327b68159716a37440985269cf584bcb1e621d3a7202be6ea05c4cfe244aeb197642555a0645fb87bf7466b2ba48", "0x00aa65dae3c8d732d10ecd2c50f8a1baf3001578f71c694e03866e9f3d49ac1e1ce70dd94a733534f106d4cec0eddd16"),
    ("abcdef0123456789", "0x121982811d2491fde9ba7ed31ef9ca474f0e1501297f68c298e9f4c0028add35aea8bb83d53c08cfc007c1e005723cd0", "0x190d119345b94fbd15497bcba94ecf7db2cbfd1e1fe7da034d26cbba169fb3968288b3fafb265f9ebd380512a71c3f2c", "0x05571a0f8d3c08d094576981f4a3b8eda0a8e771fcdcc8ecceaf1356a6acf17574518acb506e435b639353c2e14827c8", "0x0bb5e7572275c567462d91807de765611490205a941a5a6af3b1691bfe596c31225d3aabdf15faff860cb4ef17c7c3be"),
    ("q128_qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq", "0x19a84dd7248a1066f737cc34502ee5555bd3c19f2ecdb3c7d9e24dc65d4e25e50d83f0f77105e955d78f4762d33c17da", "0x0934aba516a52d8ae479939a91998299c76d39cc0c035cd18813bec433f587e2d7a4fef038260eef0cef4d02aae3eb91", "0x14f81cd421617428bc3b9fe25afbb751d934a00493524bc4e065635b0555084dd54679df1536101b2c979c0152d09192", "0x09bcccfa036b4847c9950780733633f13619994394c23ff0b32fa6b795844f4a0673e20282d07bc69641cee04f5e5662"),
    ("a512_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "0x01a6ba2f9a11fa5598b2d8ace0fbe0a0eacb65deceb476fbbcb64fd24557c2f4b18ecfc5663e54ae16a84f5ab7f62534", "0x11fca2ff525572795a801eed17eb12785887c7b63fb77a42be46ce4a34131d71f7a73e95fee3f812aea3de78b4d01569", "0x0b6798718c8aed24bc19cb27f866f1c9effcdbf92397ad6448b5c9db90d2b9da6cbabf48adc1adf59a1a28344e79d57e", "0x03a47f8e6d1763ba0cad63d6114c0accbef65707825a511b251a660a9b3994249ae4e63fac38b23da0c398689ee2ab52"),
]


def _g2_from_coords(xc0: str, xc1: str, yc0: str, yc1: str) -> G2Point:
    parts = [int(c, 16).to_bytes(FP_SIZE, "big") for c in (xc0, xc1, yc0, yc1)]
    return G2Point.from_xy_bytes_be(b"".join(parts))


class TestHashToCurveKnownAnswers:
    """Pin G2Point.hash_to_curve against the official RFC 9380 reference points."""

    @pytest.mark.parametrize("vec", RFC9380_VECTORS, ids=lambda v: v[0][:12] or "empty")
    def test_rfc9380_vector(self, vec):
        msg, xc0, xc1, yc0, yc1 = vec
        expected = _g2_from_coords(xc0, xc1, yc0, yc1)
        assert G2Point.hash_to_curve(msg.encode(), RFC9380_DST) == expected


class TestSignRoundTrip:
    """The reverse direction of TestVerify: sign with py-arkworks, then check
    py-ecc accepts it. Together the two directions form a full round-trip."""

    @pytest.mark.parametrize("msg", MESSAGES)
    def test_pyecc_verifies_arkworks_signature(self, msg):
        sk, _ = _keypair(1)
        pk = sk_to_pk(sk)
        sig = sign(sk, msg)
        assert PyEccBLS.Verify(pk, msg, sig)

    @pytest.mark.parametrize("msg", MESSAGES)
    def test_arkworks_outputs_match_pyecc(self, msg):
        # Not just "verifiable" but byte-identical: the py-arkworks public key
        # and signature must equal what py-ecc produces from the same key.
        sk, _ = _keypair(1)
        assert sk_to_pk(sk) == PyEccBLS.SkToPk(sk)
        assert sign(sk, msg) == PyEccBLS.Sign(sk, msg)
