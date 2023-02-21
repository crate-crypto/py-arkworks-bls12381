use ark_bls12_381::{G1Affine, G2Affine};
use ark_ec::pairing::Pairing;
use ark_ec::AffineRepr;
use ark_serialize::{CanonicalDeserialize, CanonicalSerialize, SerializationError};
use num_traits::identities::Zero;
use pyo3::{pyclass, pymethods, PyErr, PyResult};

const G1_COMPRESSED_SIZE: usize = 48;
const G2_COMPRESSED_SIZE: usize = 96;
const SCALAR_SIZE: usize = 32;

#[derive(Copy, Clone)]
#[pyclass]
pub struct G1Point(G1Affine);

#[pymethods]
impl G1Point {
    #[new]
    fn generator() -> Self {
        G1Point(G1Affine::generator())
    }
    #[staticmethod]
    fn identity() -> Self {
        G1Point(G1Affine::identity())
    }

    // Overriding operators
    fn __add__(&self, rhs: G1Point) -> G1Point {
        G1Point((self.0 + rhs.0).into())
    }
    fn __sub__(&self, rhs: G1Point) -> G1Point {
        G1Point((self.0 - rhs.0).into())
    }
    fn __mul__(&self, rhs: Scalar) -> G1Point {
        G1Point((self.0 * rhs.0).into())
    }
    fn __neg__(&self) -> G1Point {
        G1Point(-self.0)
    }
    fn __str__(&self) -> PyResult<String> {
        return Ok(hex::encode(self.to_compressed_bytes()?));
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
        let g1_point: G1Affine = CanonicalDeserialize::deserialize_compressed(&bytes[..])
            .map_err(serialisation_error_to_py_err)?;
        Ok(G1Point(g1_point))
    }

    #[staticmethod]
    fn from_compressed_bytes_unchecked(bytes: [u8; G1_COMPRESSED_SIZE]) -> PyResult<G1Point> {
        let g1_point: G1Affine = CanonicalDeserialize::deserialize_compressed_unchecked(&bytes[..])
            .map_err(serialisation_error_to_py_err)?;
        Ok(G1Point(g1_point))
    }
}

#[derive(Copy, Clone)]
#[pyclass]
pub struct G2Point(G2Affine);

#[pymethods]
impl G2Point {
    #[new]
    fn generator() -> Self {
        G2Point(G2Affine::generator())
    }
    #[staticmethod]
    fn identity() -> Self {
        G2Point(G2Affine::identity())
    }

    // Overriding operators
    fn __add__(&self, rhs: G2Point) -> G2Point {
        G2Point((self.0 + rhs.0).into())
    }
    fn __sub__(&self, rhs: G2Point) -> G2Point {
        G2Point((self.0 - rhs.0).into())
    }
    fn __mul__(&self, rhs: Scalar) -> G2Point {
        G2Point((self.0 * rhs.0).into())
    }
    fn __neg__(&self) -> G2Point {
        G2Point(-self.0)
    }
    fn __str__(&self) -> PyResult<String> {
        return Ok(hex::encode(self.to_compressed_bytes()?));
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
        let g2_point: G2Affine = CanonicalDeserialize::deserialize_compressed(&bytes[..])
            .map_err(serialisation_error_to_py_err)?;
        Ok(G2Point(g2_point))
    }

    #[staticmethod]
    fn from_compressed_bytes_unchecked(bytes: [u8; G2_COMPRESSED_SIZE]) -> PyResult<G2Point> {
        let g2_point: G2Affine = CanonicalDeserialize::deserialize_compressed_unchecked(&bytes[..])
            .map_err(serialisation_error_to_py_err)?;
        Ok(G2Point(g2_point))
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
        return Ok(hex::encode(self.to_bytes()?));
    }

    fn to_bytes(&self) -> PyResult<[u8; SCALAR_SIZE]> {
        let mut bytes = [0u8; SCALAR_SIZE];
        self.0
            .serialize_compressed(&mut bytes[..])
            .map_err(serialisation_error_to_py_err)?;

        Ok(bytes)
    }
    #[staticmethod]
    fn from_bytes(bytes: [u8; SCALAR_SIZE]) -> PyResult<Scalar> {
        let scalar: ark_bls12_381::Fr = CanonicalDeserialize::deserialize_compressed(&bytes[..])
            .map_err(serialisation_error_to_py_err)?;
        Ok(Scalar(scalar))
    }

    #[staticmethod]
    fn from_bytes_unchecked(bytes: [u8; SCALAR_SIZE]) -> PyResult<Scalar> {
        let scalar: ark_bls12_381::Fr =
            CanonicalDeserialize::deserialize_compressed_unchecked(&bytes[..])
                .map_err(serialisation_error_to_py_err)?;
        Ok(Scalar(scalar))
    }
}

#[derive(Copy, Clone)]
#[pyclass]
pub struct GT(ark_bls12_381::Fq12);

#[pymethods]
impl GT {
    #[staticmethod]
    fn pairing(g1s: Vec<G1Point>, g2s: Vec<G2Point>) -> bool {
        let g1_inner = g1s.into_iter().map(|g1| g1.0);
        let g2_inner = g2s.into_iter().map(|g2| g2.0);

        ark_bls12_381::Bls12_381::multi_pairing(g1_inner, g2_inner).is_zero()
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
