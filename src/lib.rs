mod wrapper;
use wrapper::{G1Point, G2Point, Scalar, GT};

use pyo3::prelude::*;

#[pymodule(gil_used = false)]
mod py_arkworks_bls12381 {
    #[pymodule_export]
    use super::G1Point;
    #[pymodule_export]
    use super::G2Point;
    #[pymodule_export]
    use super::GT;
    #[pymodule_export]
    use super::Scalar;
}
