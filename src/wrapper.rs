use ark_bls12_381::{Fq, Fq2, G1Affine, G1Projective, G2Affine, G2Projective};
use ark_ec::hashing::curve_maps::wb::WBMap;
use ark_ec::hashing::map_to_curve_hasher::MapToCurve;
use ark_ec::pairing::{Pairing, PairingOutput};
use ark_ec::{AffineRepr, PrimeGroup, ScalarMul, VariableBaseMSM};
use ark_ff::{Field, One, PrimeField};
use ark_serialize::{CanonicalDeserialize, CanonicalSerialize, SerializationError};
use num_bigint::BigUint;
use num_traits::identities::Zero;
use pyo3::{exceptions, pyclass, pymethods, PyErr, PyResult, Python};
use rayon::prelude::{IntoParallelIterator, ParallelIterator};
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};
use std::str::FromStr;

const G1_COMPRESSED_SIZE: usize = 48;
const G2_COMPRESSED_SIZE: usize = 96;
const SCALAR_SIZE: usize = 32;

const FP_SIZE: usize = 48;
const G1_UNCOMPRESSED_SIZE: usize = 96; // 2 * FP_SIZE
const G2_UNCOMPRESSED_SIZE: usize = 192; // 4 * FP_SIZE

#[derive(Copy, Clone)]
enum Endian {
    Big,
    Little,
}

fn read_fp(bytes: &[u8; FP_SIZE], endian: Endian) -> PyResult<Fq> {
    let mut buf = *bytes;
    if matches!(endian, Endian::Big) {
        buf.reverse();
    }
    Fq::deserialize_uncompressed(&buf[..]).map_err(serialisation_error_to_py_err)
}

fn encode_fp(fp: &Fq, endian: Endian) -> PyResult<[u8; FP_SIZE]> {
    let mut buf = [0u8; FP_SIZE];
    fp.serialize_uncompressed(&mut buf[..])
        .map_err(serialisation_error_to_py_err)?;
    if matches!(endian, Endian::Big) {
        buf.reverse();
    }
    Ok(buf)
}

fn read_fp2(bytes: &[u8; 2 * FP_SIZE], endian: Endian) -> PyResult<Fq2> {
    let c0 = read_fp(bytes[..FP_SIZE].try_into().unwrap(), endian)?;
    let c1 = read_fp(bytes[FP_SIZE..].try_into().unwrap(), endian)?;
    Ok(Fq2::new(c0, c1))
}

#[derive(Copy, Clone)]
#[pyclass]
pub struct G1Point(G1Projective);

#[pymethods]
impl G1Point {
    #[new]
    fn generator() -> Self {
        G1Point(G1Projective::generator())
    }
    #[staticmethod]
    fn identity() -> Self {
        G1Point(G1Affine::identity().into())
    }

    // Overriding operators
    fn __add__(&self, rhs: G1Point) -> G1Point {
        G1Point(self.0 + rhs.0)
    }
    fn __sub__(&self, rhs: G1Point) -> G1Point {
        G1Point(self.0 - rhs.0)
    }
    fn __mul__(&self, rhs: Scalar) -> G1Point {
        G1Point(self.0 * rhs.0)
    }
    fn __neg__(&self) -> G1Point {
        G1Point(-self.0)
    }
    fn __str__(&self) -> PyResult<String> {
        Ok(hex::encode(self.to_compressed_bytes()?))
    }
    fn __richcmp__(&self, other: G1Point, op: pyclass::CompareOp) -> PyResult<bool> {
        match op {
            pyclass::CompareOp::Eq => Ok(self.0 == other.0),
            pyclass::CompareOp::Ne => Ok(self.0 != other.0),
            _ => Err(exceptions::PyValueError::new_err(
                "comparison operator not implemented".to_owned(),
            )),
        }
    }
    fn __hash__(&self) -> PyResult<i64> {
        let bytes = self.to_compressed_bytes()?;
        let mut hasher = DefaultHasher::new();
        bytes.hash(&mut hasher);
        Ok(hasher.finish() as i64)
    }
    fn __repr__(&self) -> PyResult<String> {
        let hex = hex::encode(self.to_compressed_bytes()?);
        Ok(format!("G1Point(0x{}...{})", &hex[..8], &hex[hex.len() - 8..]))
    }

    fn is_in_subgroup(&self) -> bool {
        let affine: G1Affine = self.0.into();
        affine.is_in_correct_subgroup_assuming_on_curve()
    }

    fn to_compressed_bytes(&self) -> PyResult<[u8; G1_COMPRESSED_SIZE]> {
        let mut bytes = [0u8; G1_COMPRESSED_SIZE];
        self.0
            .serialize_compressed(&mut bytes[..])
            .map_err(serialisation_error_to_py_err)?;

        Ok(bytes)
    }

    #[staticmethod]
    fn from_compressed_bytes(data: [u8; G1_COMPRESSED_SIZE]) -> PyResult<G1Point> {
        let g1_point: G1Projective = CanonicalDeserialize::deserialize_compressed(&data[..])
            .map_err(serialisation_error_to_py_err)?;
        Ok(G1Point(g1_point))
    }

    #[staticmethod]
    fn from_compressed_bytes_unchecked(data: [u8; G1_COMPRESSED_SIZE]) -> PyResult<G1Point> {
        let g1_point: G1Projective =
            CanonicalDeserialize::deserialize_compressed_unchecked(&data[..])
                .map_err(serialisation_error_to_py_err)?;
        Ok(G1Point(g1_point))
    }

    /// Serialize to 96-byte uncompressed format (big-endian x || y, 48 bytes each).
    /// Point-at-infinity is encoded as 96 zero bytes.
    fn to_xy_bytes_be(&self) -> PyResult<[u8; G1_UNCOMPRESSED_SIZE]> {
        self.to_xy_bytes_impl(Endian::Big)
    }

    /// Serialize to 96-byte uncompressed format (little-endian x || y, 48 bytes each).
    /// Point-at-infinity is encoded as 96 zero bytes.
    fn to_xy_bytes_le(&self) -> PyResult<[u8; G1_UNCOMPRESSED_SIZE]> {
        self.to_xy_bytes_impl(Endian::Little)
    }

    /// Deserialize from 96-byte uncompressed big-endian format (x || y) with on-curve and subgroup checks.
    #[staticmethod]
    fn from_xy_bytes_be(data: [u8; G1_UNCOMPRESSED_SIZE]) -> PyResult<G1Point> {
        Self::from_xy_bytes_impl(data, Endian::Big, true)
    }

    /// Deserialize from 96-byte uncompressed little-endian format (x || y) with on-curve and subgroup checks.
    #[staticmethod]
    fn from_xy_bytes_le(data: [u8; G1_UNCOMPRESSED_SIZE]) -> PyResult<G1Point> {
        Self::from_xy_bytes_impl(data, Endian::Little, true)
    }

    /// Deserialize from 96-byte uncompressed big-endian format (x || y) with on-curve check only (no subgroup check).
    #[staticmethod]
    fn from_xy_bytes_unchecked_be(data: [u8; G1_UNCOMPRESSED_SIZE]) -> PyResult<G1Point> {
        Self::from_xy_bytes_impl(data, Endian::Big, false)
    }

    /// Deserialize from 96-byte uncompressed little-endian format (x || y) with on-curve check only (no subgroup check).
    #[staticmethod]
    fn from_xy_bytes_unchecked_le(data: [u8; G1_UNCOMPRESSED_SIZE]) -> PyResult<G1Point> {
        Self::from_xy_bytes_impl(data, Endian::Little, false)
    }

    /// Map a big-endian field element to a G1 point using SWU map with cofactor clearing.
    #[staticmethod]
    fn map_from_fp_be(fp_bytes: [u8; FP_SIZE]) -> PyResult<G1Point> {
        Self::map_from_fp_impl(fp_bytes, Endian::Big)
    }

    /// Map a little-endian field element to a G1 point using SWU map with cofactor clearing.
    #[staticmethod]
    fn map_from_fp_le(fp_bytes: [u8; FP_SIZE]) -> PyResult<G1Point> {
        Self::map_from_fp_impl(fp_bytes, Endian::Little)
    }

    #[staticmethod]
    fn multiexp_unchecked(
        py: Python,
        points: Vec<G1Point>,
        scalars: Vec<Scalar>,
    ) -> PyResult<G1Point> {
        py.detach(|| {
            let points: Vec<_> = points.into_par_iter().map(|point| point.0).collect();
            let scalars: Vec<_> = scalars.into_par_iter().map(|scalar| scalar.0).collect();

            // Convert the points to affine.
            // TODO: we could have a G1AffinePoint struct and then a G1ProjectivePoint
            // TODO struct, so that this cost is explicit
            let affine_points = G1Projective::batch_convert_to_mul_base(&points);
            let result = G1Projective::msm_unchecked(&affine_points, &scalars);
            Ok(G1Point(result))
        })
    }
}

impl G1Point {
    fn to_xy_bytes_impl(&self, endian: Endian) -> PyResult<[u8; G1_UNCOMPRESSED_SIZE]> {
        let affine: G1Affine = self.0.into();
        let mut result = [0u8; G1_UNCOMPRESSED_SIZE];

        if let Some((x, y)) = affine.xy() {
            let x_bytes = encode_fp(&x, endian)?;
            let y_bytes = encode_fp(&y, endian)?;
            result[..FP_SIZE].copy_from_slice(&x_bytes);
            result[FP_SIZE..].copy_from_slice(&y_bytes);
        }

        Ok(result)
    }

    fn from_xy_bytes_impl(
        bytes: [u8; G1_UNCOMPRESSED_SIZE],
        endian: Endian,
        check_subgroup: bool,
    ) -> PyResult<G1Point> {
        if bytes.iter().all(|&b| b == 0) {
            return Ok(G1Point(G1Affine::identity().into()));
        }

        let x = read_fp(bytes[..FP_SIZE].try_into().unwrap(), endian)?;
        let y = read_fp(bytes[FP_SIZE..].try_into().unwrap(), endian)?;
        let point = G1Affine::new_unchecked(x, y);

        if !point.is_on_curve() {
            return Err(exceptions::PyValueError::new_err(
                "point is not on the G1 curve",
            ));
        }
        if check_subgroup && !point.is_in_correct_subgroup_assuming_on_curve() {
            return Err(exceptions::PyValueError::new_err(
                "point is not in the correct G1 subgroup",
            ));
        }

        Ok(G1Point(point.into()))
    }

    fn map_from_fp_impl(fp_bytes: [u8; FP_SIZE], endian: Endian) -> PyResult<G1Point> {
        let fp = read_fp(&fp_bytes, endian)?;
        let point = WBMap::<ark_bls12_381::g1::Config>::map_to_curve(fp).map_err(|e| {
            exceptions::PyValueError::new_err(format!("map_to_curve failed: {e}"))
        })?;
        let cleared = point.clear_cofactor();
        Ok(G1Point(cleared.into()))
    }
}

#[derive(Copy, Clone)]
#[pyclass]
pub struct G2Point(G2Projective);

#[pymethods]
impl G2Point {
    #[new]
    fn generator() -> Self {
        G2Point(G2Affine::generator().into())
    }
    #[staticmethod]
    fn identity() -> Self {
        G2Point(G2Affine::identity().into())
    }

    // Overriding operators
    fn __add__(&self, rhs: G2Point) -> G2Point {
        G2Point(self.0 + rhs.0)
    }
    fn __sub__(&self, rhs: G2Point) -> G2Point {
        G2Point(self.0 - rhs.0)
    }
    fn __mul__(&self, rhs: Scalar) -> G2Point {
        G2Point(self.0 * rhs.0)
    }
    fn __neg__(&self) -> G2Point {
        G2Point(-self.0)
    }
    fn __str__(&self) -> PyResult<String> {
        Ok(hex::encode(self.to_compressed_bytes()?))
    }
    fn __richcmp__(&self, other: G2Point, op: pyclass::CompareOp) -> PyResult<bool> {
        match op {
            pyclass::CompareOp::Eq => Ok(self.0 == other.0),
            pyclass::CompareOp::Ne => Ok(self.0 != other.0),
            _ => Err(exceptions::PyValueError::new_err(
                "comparison operator not implemented".to_owned(),
            )),
        }
    }
    fn __hash__(&self) -> PyResult<i64> {
        let bytes = self.to_compressed_bytes()?;
        let mut hasher = DefaultHasher::new();
        bytes.hash(&mut hasher);
        Ok(hasher.finish() as i64)
    }
    fn __repr__(&self) -> PyResult<String> {
        let hex = hex::encode(self.to_compressed_bytes()?);
        Ok(format!("G2Point(0x{}...{})", &hex[..8], &hex[hex.len() - 8..]))
    }

    fn is_in_subgroup(&self) -> bool {
        let affine: G2Affine = self.0.into();
        affine.is_in_correct_subgroup_assuming_on_curve()
    }

    fn to_compressed_bytes(&self) -> PyResult<[u8; G2_COMPRESSED_SIZE]> {
        let mut bytes = [0u8; G2_COMPRESSED_SIZE];
        self.0
            .serialize_compressed(&mut bytes[..])
            .map_err(serialisation_error_to_py_err)?;

        Ok(bytes)
    }

    #[staticmethod]
    fn from_compressed_bytes(data: [u8; G2_COMPRESSED_SIZE]) -> PyResult<G2Point> {
        let g2_point: G2Projective = CanonicalDeserialize::deserialize_compressed(&data[..])
            .map_err(serialisation_error_to_py_err)?;
        Ok(G2Point(g2_point))
    }

    #[staticmethod]
    fn from_compressed_bytes_unchecked(data: [u8; G2_COMPRESSED_SIZE]) -> PyResult<G2Point> {
        let g2_point: G2Projective =
            CanonicalDeserialize::deserialize_compressed_unchecked(&data[..])
                .map_err(serialisation_error_to_py_err)?;
        Ok(G2Point(g2_point))
    }

    /// Serialize to 192-byte uncompressed format (big-endian x.c0 || x.c1 || y.c0 || y.c1, 48 bytes each).
    /// Point-at-infinity is encoded as 192 zero bytes.
    fn to_xy_bytes_be(&self) -> PyResult<[u8; G2_UNCOMPRESSED_SIZE]> {
        self.to_xy_bytes_impl(Endian::Big)
    }

    /// Serialize to 192-byte uncompressed format (little-endian x.c0 || x.c1 || y.c0 || y.c1, 48 bytes each).
    /// Point-at-infinity is encoded as 192 zero bytes.
    fn to_xy_bytes_le(&self) -> PyResult<[u8; G2_UNCOMPRESSED_SIZE]> {
        self.to_xy_bytes_impl(Endian::Little)
    }

    /// Deserialize from 192-byte uncompressed big-endian format (x.c0 || x.c1 || y.c0 || y.c1)
    /// with on-curve and subgroup checks.
    #[staticmethod]
    fn from_xy_bytes_be(data: [u8; G2_UNCOMPRESSED_SIZE]) -> PyResult<G2Point> {
        Self::from_xy_bytes_impl(data, Endian::Big, true)
    }

    /// Deserialize from 192-byte uncompressed little-endian format (x.c0 || x.c1 || y.c0 || y.c1)
    /// with on-curve and subgroup checks.
    #[staticmethod]
    fn from_xy_bytes_le(data: [u8; G2_UNCOMPRESSED_SIZE]) -> PyResult<G2Point> {
        Self::from_xy_bytes_impl(data, Endian::Little, true)
    }

    /// Deserialize from 192-byte uncompressed big-endian format (x.c0 || x.c1 || y.c0 || y.c1)
    /// with on-curve check only (no subgroup check).
    #[staticmethod]
    fn from_xy_bytes_unchecked_be(data: [u8; G2_UNCOMPRESSED_SIZE]) -> PyResult<G2Point> {
        Self::from_xy_bytes_impl(data, Endian::Big, false)
    }

    /// Deserialize from 192-byte uncompressed little-endian format (x.c0 || x.c1 || y.c0 || y.c1)
    /// with on-curve check only (no subgroup check).
    #[staticmethod]
    fn from_xy_bytes_unchecked_le(data: [u8; G2_UNCOMPRESSED_SIZE]) -> PyResult<G2Point> {
        Self::from_xy_bytes_impl(data, Endian::Little, false)
    }

    /// Map a big-endian Fp2 element to a G2 point using SWU map with cofactor clearing.
    #[staticmethod]
    fn map_from_fp2_be(fp2_bytes: [u8; 2 * FP_SIZE]) -> PyResult<G2Point> {
        Self::map_from_fp2_impl(fp2_bytes, Endian::Big)
    }

    /// Map a little-endian Fp2 element to a G2 point using SWU map with cofactor clearing.
    #[staticmethod]
    fn map_from_fp2_le(fp2_bytes: [u8; 2 * FP_SIZE]) -> PyResult<G2Point> {
        Self::map_from_fp2_impl(fp2_bytes, Endian::Little)
    }

    #[staticmethod]
    fn multiexp_unchecked(
        py: Python,
        points: Vec<G2Point>,
        scalars: Vec<Scalar>,
    ) -> PyResult<G2Point> {
        py.detach(|| {
            let points: Vec<_> = points.into_par_iter().map(|point| point.0).collect();
            let scalars: Vec<_> = scalars.into_par_iter().map(|scalar| scalar.0).collect();

            // Convert the points to affine.
            // TODO: we could have a G2AffinePoint struct and then a G2ProjectivePoint
            // TODO struct, so that this cost is explicit
            let affine_points = G2Projective::batch_convert_to_mul_base(&points);
            let result = G2Projective::msm_unchecked(&affine_points, &scalars);
            Ok(G2Point(result))
        })
    }
}

impl G2Point {
    fn to_xy_bytes_impl(&self, endian: Endian) -> PyResult<[u8; G2_UNCOMPRESSED_SIZE]> {
        let affine: G2Affine = self.0.into();
        let mut result = [0u8; G2_UNCOMPRESSED_SIZE];

        if let Some((x, y)) = affine.xy() {
            let x_c0_bytes = encode_fp(&x.c0, endian)?;
            let x_c1_bytes = encode_fp(&x.c1, endian)?;
            let y_c0_bytes = encode_fp(&y.c0, endian)?;
            let y_c1_bytes = encode_fp(&y.c1, endian)?;
            result[..FP_SIZE].copy_from_slice(&x_c0_bytes);
            result[FP_SIZE..2 * FP_SIZE].copy_from_slice(&x_c1_bytes);
            result[2 * FP_SIZE..3 * FP_SIZE].copy_from_slice(&y_c0_bytes);
            result[3 * FP_SIZE..].copy_from_slice(&y_c1_bytes);
        }

        Ok(result)
    }

    fn from_xy_bytes_impl(
        bytes: [u8; G2_UNCOMPRESSED_SIZE],
        endian: Endian,
        check_subgroup: bool,
    ) -> PyResult<G2Point> {
        if bytes.iter().all(|&b| b == 0) {
            return Ok(G2Point(G2Affine::identity().into()));
        }

        let x = read_fp2(bytes[..2 * FP_SIZE].try_into().unwrap(), endian)?;
        let y = read_fp2(bytes[2 * FP_SIZE..].try_into().unwrap(), endian)?;
        let point = G2Affine::new_unchecked(x, y);

        if !point.is_on_curve() {
            return Err(exceptions::PyValueError::new_err(
                "point is not on the G2 curve",
            ));
        }
        if check_subgroup && !point.is_in_correct_subgroup_assuming_on_curve() {
            return Err(exceptions::PyValueError::new_err(
                "point is not in the correct G2 subgroup",
            ));
        }

        Ok(G2Point(point.into()))
    }

    fn map_from_fp2_impl(fp2_bytes: [u8; 2 * FP_SIZE], endian: Endian) -> PyResult<G2Point> {
        let fp2 = read_fp2(&fp2_bytes, endian)?;
        let point = WBMap::<ark_bls12_381::g2::Config>::map_to_curve(fp2).map_err(|e| {
            exceptions::PyValueError::new_err(format!("map_to_curve failed: {e}"))
        })?;
        let cleared = point.clear_cofactor();
        Ok(G2Point(cleared.into()))
    }
}

#[derive(Copy, Clone)]
#[pyclass]
pub struct Scalar(ark_bls12_381::Fr);

#[pymethods]
impl Scalar {
    #[new]
    fn new(integer: BigUint) -> PyResult<Self> {
        let fr = ark_bls12_381::Fr::from_str(&*integer.to_string())
            .map_err(|_| exceptions::PyValueError::new_err("failed to parse integer as a scalar field element"))?;
        Ok(Scalar(fr))
    }

    // Overriding operators
    fn __add__(&self, rhs: Scalar) -> Scalar {
        Scalar(self.0 + rhs.0)
    }
    fn __sub__(&self, rhs: Scalar) -> Scalar {
        Scalar(self.0 - rhs.0)
    }
    fn __mul__(&self, rhs: Scalar) -> Scalar {
        Scalar(self.0 * rhs.0)
    }
    fn __truediv__(&self, rhs: Scalar) -> PyResult<Scalar> {
        if rhs.is_zero() {
            let message = "Cannot divide by zero";
            return Err(exceptions::PyZeroDivisionError::new_err(message));
        }
        Ok(Scalar(self.0 / rhs.0))
    }
    fn __neg__(&self) -> Scalar {
        Scalar(-self.0)
    }
    fn __str__(&self) -> PyResult<String> {
        Ok(hex::encode(self.to_le_bytes()?))
    }
    fn __richcmp__(&self, other: Scalar, op: pyclass::CompareOp) -> PyResult<bool> {
        match op {
            pyclass::CompareOp::Eq => Ok(self.0 == other.0),
            pyclass::CompareOp::Ne => Ok(self.0 != other.0),
            _ => Err(exceptions::PyValueError::new_err(
                "comparison operator not implemented".to_owned(),
            )),
        }
    }
    fn __int__(&self) -> BigUint {
        BigUint::from(self.0.into_bigint())
    }
    fn __hash__(&self) -> PyResult<i64> {
        let bytes = self.to_le_bytes()?;
        let mut hasher = DefaultHasher::new();
        bytes.hash(&mut hasher);
        Ok(hasher.finish() as i64)
    }
    fn __repr__(&self) -> String {
        format!("Scalar({})", BigUint::from(self.0.into_bigint()))
    }

    fn pow(&self, exp: Scalar) -> Scalar {
        Scalar(self.0.pow(exp.0.into_bigint()))
    }
    fn square(&self) -> Scalar {
        Scalar(self.0.square())
    }
    fn inverse(&self) -> PyResult<Scalar> {
        self.0
            .inverse()
            .map(Scalar)
            .ok_or_else(|| exceptions::PyZeroDivisionError::new_err("Cannot invert zero"))
    }
    fn is_zero(&self) -> bool {
        self.0.is_zero()
    }
    fn is_one(&self) -> bool {
        self.0.is_one()
    }

    fn to_le_bytes(&self) -> PyResult<[u8; SCALAR_SIZE]> {
        let mut bytes = [0u8; SCALAR_SIZE];
        self.0
            .serialize_compressed(&mut bytes[..])
            .map_err(serialisation_error_to_py_err)?;

        Ok(bytes)
    }
    #[staticmethod]
    fn from_le_bytes(data: [u8; SCALAR_SIZE]) -> PyResult<Scalar> {
        let scalar: ark_bls12_381::Fr = CanonicalDeserialize::deserialize_compressed(&data[..])
            .map_err(serialisation_error_to_py_err)?;
        Ok(Scalar(scalar))
    }

    /// Serialize scalar as 32-byte big-endian.
    fn to_be_bytes(&self) -> PyResult<[u8; SCALAR_SIZE]> {
        let mut bytes = self.to_le_bytes()?;
        bytes.reverse();
        Ok(bytes)
    }

    /// Deserialize scalar from 32-byte big-endian.
    /// Rejects non-canonical values (>= subgroup order).
    #[staticmethod]
    fn from_be_bytes(data: [u8; SCALAR_SIZE]) -> PyResult<Scalar> {
        let mut le_data = data;
        le_data.reverse();
        let scalar: ark_bls12_381::Fr =
            CanonicalDeserialize::deserialize_compressed(&le_data[..])
                .map_err(serialisation_error_to_py_err)?;
        Ok(Scalar(scalar))
    }

    /// Deserialize scalar from little-endian bytes with modular reduction.
    /// Accepts arbitrary-length input; the value is reduced mod the subgroup order.
    #[staticmethod]
    fn from_le_bytes_mod_order(data: &[u8]) -> Scalar {
        Scalar(ark_bls12_381::Fr::from_le_bytes_mod_order(data))
    }

    /// Deserialize scalar from big-endian bytes with modular reduction.
    /// Accepts arbitrary-length input; the value is reduced mod the subgroup order.
    #[staticmethod]
    fn from_be_bytes_mod_order(data: &[u8]) -> Scalar {
        let mut le_data = data.to_vec();
        le_data.reverse();
        Scalar(ark_bls12_381::Fr::from_le_bytes_mod_order(&le_data))
    }
}

#[derive(Copy, Clone)]
#[pyclass]
pub struct GT(ark_bls12_381::Fq12);

#[pymethods]
impl GT {
    #[new]
    fn generator() -> GT {
        GT(PairingOutput::<ark_bls12_381::Bls12_381>::generator().0)
    }

    #[staticmethod]
    fn zero() -> GT {
        GT(ark_bls12_381::Fq12::zero())
    }
    #[staticmethod]
    fn one() -> GT {
        GT(ark_bls12_381::Fq12::one())
    }

    #[staticmethod]
    fn multi_pairing(py: Python, g1s: Vec<G1Point>, g2s: Vec<G2Point>) -> PyResult<GT> {
        if g1s.len() != g2s.len() {
            return Err(exceptions::PyValueError::new_err(
                "g1s and g2s must have the same length",
            ));
        }
        py.detach(|| {
            let g1_inner: Vec<G1Affine> = g1s.into_par_iter().map(|g1| g1.0.into()).collect();
            let g2_inner: Vec<G2Affine> = g2s.into_par_iter().map(|g2| g2.0.into()).collect();
            Ok(GT(ark_bls12_381::Bls12_381::multi_pairing(g1_inner, g2_inner).0))
        })
    }
    #[staticmethod]
    fn pairing(py: Python, g1: G1Point, g2: G2Point) -> GT {
        py.detach(|| GT(ark_bls12_381::Bls12_381::pairing(g1.0, g2.0).0))
    }

    /// Check if the product of pairings equals the identity.
    /// Returns true if e(g1s[0], g2s[0]) * ... * e(g1s[n], g2s[n]) == 1.
    /// Returns true for empty input.
    #[staticmethod]
    fn pairing_check(py: Python, g1s: Vec<G1Point>, g2s: Vec<G2Point>) -> PyResult<bool> {
        if g1s.len() != g2s.len() {
            return Err(exceptions::PyValueError::new_err(
                "g1s and g2s must have the same length",
            ));
        }
        if g1s.is_empty() {
            return Ok(true);
        }
        py.detach(|| {
            let g1_inner: Vec<G1Affine> = g1s.into_par_iter().map(|g1| g1.0.into()).collect();
            let g2_inner: Vec<G2Affine> = g2s.into_par_iter().map(|g2| g2.0.into()).collect();
            Ok(ark_bls12_381::Bls12_381::multi_pairing(g1_inner, g2_inner)
                .0
                .is_one())
        })
    }

    // Overriding operators
    fn __add__(&self, rhs: GT) -> GT {
        GT(self.0 + rhs.0)
    }
    fn __sub__(&self, rhs: GT) -> GT {
        GT(self.0 - rhs.0)
    }
    fn __mul__(&self, rhs: GT) -> GT {
        GT(self.0 * rhs.0)
    }
    fn __neg__(&self) -> GT {
        GT(-self.0)
    }
    fn __str__(&self) -> PyResult<String> {
        let mut bytes = Vec::new();
        self.0
            .serialize_compressed(&mut bytes)
            .map_err(serialisation_error_to_py_err)?;
        Ok(hex::encode(bytes))
    }
    fn __richcmp__(&self, other: GT, op: pyclass::CompareOp) -> PyResult<bool> {
        match op {
            pyclass::CompareOp::Eq => Ok(self.0 == other.0),
            pyclass::CompareOp::Ne => Ok(self.0 != other.0),
            _ => Err(exceptions::PyValueError::new_err(
                "comparison operator not implemented".to_owned(),
            )),
        }
    }
    fn __hash__(&self) -> PyResult<i64> {
        let mut bytes = Vec::new();
        self.0
            .serialize_compressed(&mut bytes)
            .map_err(serialisation_error_to_py_err)?;
        let mut hasher = DefaultHasher::new();
        bytes.hash(&mut hasher);
        Ok(hasher.finish() as i64)
    }
    fn __repr__(&self) -> PyResult<String> {
        let mut bytes = Vec::new();
        self.0
            .serialize_compressed(&mut bytes)
            .map_err(serialisation_error_to_py_err)?;
        let hex = hex::encode(bytes);
        Ok(format!("GT(0x{}...{})", &hex[..8], &hex[hex.len() - 8..]))
    }
}

fn serialisation_error_to_py_err(serialisation_error: SerializationError) -> PyErr {
    use pyo3::exceptions::{PyIOError, PyValueError};
    match serialisation_error {
        SerializationError::NotEnoughSpace => PyValueError::new_err(wrap_err_string(
            "not enough space has been allocated to serialise the object".to_string(),
        )),
        SerializationError::InvalidData => PyValueError::new_err(wrap_err_string(
            "serialised data seems to be invalid".to_string(),
        )),
        SerializationError::UnexpectedFlags => PyValueError::new_err(wrap_err_string(
            "got an unexpected flag in serialised data, check if data is malformed".to_string(),
        )),
        SerializationError::IoError(err) => PyIOError::new_err(wrap_err_string(err.to_string())),
    }
}

fn wrap_err_string(err: String) -> String {
    format!("Err From Rust: {err}")
}
