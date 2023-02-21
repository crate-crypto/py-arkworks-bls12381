# py_arkworks_bls12381

## Installation

To install you will need maturin to run the builds:

```
pip install maturin
```

## Usage (Development)

- First activate the virtual environment

```
 source .env/bin/activate
```

- Next build the rust package and install it in your virtual environment

```
maturin develop
```

- Now run a file in the examples folder

```
python3 examples/g1.py
```