mod wrapper;
use pyo3::prelude::*;
use wrapper::{G1Point, G2Point, Scalar, GT};

/// A Python module implemented in Rust.
#[pymodule]
fn word_counter(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<G1Point>()?;
    m.add_class::<G2Point>()?;
    m.add_class::<GT>()?;
    m.add_class::<Scalar>()?;

    Ok(())
}
