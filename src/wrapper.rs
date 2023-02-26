use ark_bls12_381::{G1Affine, G1Projective, G2Affine, G2Projective};
use ark_ec::pairing::{Pairing, PairingOutput};
use ark_ec::{AffineRepr, Group, ScalarMul, VariableBaseMSM};
use ark_ff::One;
use ark_serialize::{CanonicalDeserialize, CanonicalSerialize, SerializationError};
use num_traits::identities::Zero;
use pyo3::{exceptions, pyclass, pymethods, PyErr, PyResult, Python};
use rayon::prelude::{IntoParallelIterator, ParallelIterator};
const G1_COMPRESSED_SIZE: usize = 48;
const G2_COMPRESSED_SIZE: usize = 96;
const SCALAR_SIZE: usize = 32;

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
        G1Point((self.0 - rhs.0).into())
    }
    fn __mul__(&self, rhs: Scalar) -> G1Point {
        G1Point(self.0 * rhs.0)
    }
    fn __neg__(&self) -> G1Point {
        G1Point(-self.0)
    }
    fn __str__(&self) -> PyResult<String> {
        return Ok(hex::encode(self.to_compressed_bytes()?));
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

    fn to_compressed_bytes(&self) -> PyResult<[u8; G1_COMPRESSED_SIZE]> {
        let mut bytes = [0u8; G1_COMPRESSED_SIZE];
        self.0
            .serialize_compressed(&mut bytes[..])
            .map_err(serialisation_error_to_py_err)?;

        Ok(bytes)
    }

    #[staticmethod]
    fn from_compressed_bytes(bytes: [u8; G1_COMPRESSED_SIZE]) -> PyResult<G1Point> {
        let g1_point: G1Projective = CanonicalDeserialize::deserialize_compressed(&bytes[..])
            .map_err(serialisation_error_to_py_err)?;
        Ok(G1Point(g1_point))
    }

    #[staticmethod]
    fn from_compressed_bytes_unchecked(bytes: [u8; G1_COMPRESSED_SIZE]) -> PyResult<G1Point> {
        let g1_point: G1Projective =
            CanonicalDeserialize::deserialize_compressed_unchecked(&bytes[..])
                .map_err(serialisation_error_to_py_err)?;
        Ok(G1Point(g1_point))
    }

    #[staticmethod]
    fn multiexp_unchecked(py : Python, points: Vec<G1Point>, scalars: Vec<Scalar>) -> PyResult<G1Point> {
        py.allow_threads(|| {
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
        return Ok(hex::encode(self.to_compressed_bytes()?));
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

    fn to_compressed_bytes(&self) -> PyResult<[u8; G2_COMPRESSED_SIZE]> {
        let mut bytes = [0u8; G2_COMPRESSED_SIZE];
        self.0
            .serialize_compressed(&mut bytes[..])
            .map_err(serialisation_error_to_py_err)?;

        Ok(bytes)
    }

    #[staticmethod]
    fn from_compressed_bytes(bytes: [u8; G2_COMPRESSED_SIZE]) -> PyResult<G2Point> {
        let g2_point: G2Projective = CanonicalDeserialize::deserialize_compressed(&bytes[..])
            .map_err(serialisation_error_to_py_err)?;
        Ok(G2Point(g2_point))
    }

    #[staticmethod]
    fn from_compressed_bytes_unchecked(bytes: [u8; G2_COMPRESSED_SIZE]) -> PyResult<G2Point> {
        let g2_point: G2Projective =
            CanonicalDeserialize::deserialize_compressed_unchecked(&bytes[..])
                .map_err(serialisation_error_to_py_err)?;
        Ok(G2Point(g2_point))
    }

    #[staticmethod]
    fn multiexp_unchecked(py: Python,points: Vec<G2Point>, scalars: Vec<Scalar>) -> PyResult<G2Point> {
        py.allow_threads(|| {
            let points: Vec<_> = points.into_iter().map(|point| point.0).collect();
            let scalars: Vec<_> = scalars.into_iter().map(|scalar| scalar.0).collect();
    
            // Convert the points to affine.
            // TODO: we could have a G2AffinePoint struct and then a G2ProjectivePoint
            // TODO struct, so that this cost is explicit
            let affine_points = G2Projective::batch_convert_to_mul_base(&points);
            let result = G2Projective::msm_unchecked(&affine_points, &scalars);
            Ok(G2Point(result))
        })
    }
}

#[derive(Copy, Clone)]
#[pyclass]
pub struct Scalar(ark_bls12_381::Fr);

#[pymethods]
impl Scalar {
    #[new]
    fn new(integer: u128) -> Self {
        Scalar(ark_bls12_381::Fr::from(integer))
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
    fn __neg__(&self) -> Scalar {
        Scalar(-self.0)
    }
    fn __str__(&self) -> PyResult<String> {
        return Ok(hex::encode(self.to_le_bytes()?));
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

    fn square(&self) -> Scalar {
        use ark_ff::fields::Field;
        Scalar(self.0.square())
    }
    fn inverse(&self) -> Scalar {
        use ark_ff::fields::Field;
        Scalar(self.0.inverse().unwrap_or_default())
    }
    fn is_zero(&self) -> bool {
        self.0.is_zero()
    }

    fn to_le_bytes(&self) -> PyResult<[u8; SCALAR_SIZE]> {
        let mut bytes = [0u8; SCALAR_SIZE];
        self.0
            .serialize_compressed(&mut bytes[..])
            .map_err(serialisation_error_to_py_err)?;

        Ok(bytes)
    }
    #[staticmethod]
    fn from_le_bytes(bytes: [u8; SCALAR_SIZE]) -> PyResult<Scalar> {
        let scalar: ark_bls12_381::Fr = CanonicalDeserialize::deserialize_compressed(&bytes[..])
            .map_err(serialisation_error_to_py_err)?;
        Ok(Scalar(scalar))
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
    fn multi_pairing(py:Python,g1s: Vec<G1Point>, g2s: Vec<G2Point>) -> GT {
        py.allow_threads(||{
            let g1_inner : Vec<G1Affine>= g1s.into_par_iter().map(|g1| g1.0.into()).collect();
            let g2_inner : Vec<G2Affine>= g2s.into_par_iter().map(|g2| g2.0.into()).collect();
            GT(ark_bls12_381::Bls12_381::multi_pairing(g1_inner, g2_inner).0)
        })
    }
    #[staticmethod]
    fn pairing(py : Python, g1: G1Point, g2: G2Point) -> GT {
        py.allow_threads(|| {
            GT(ark_bls12_381::Bls12_381::pairing(g1.0, g2.0).0)
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
