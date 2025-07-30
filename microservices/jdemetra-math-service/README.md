# Mathematical Operations Service

High-performance mathematical operations service using gRPC.

## Features

- Matrix operations (multiplication, inversion, decomposition)
- Polynomial operations (evaluation, roots, arithmetic)
- Linear algebra solvers
- Optimized with NumPy, SciPy, and Numba

## API

The service uses gRPC for high-performance communication. See `proto/math_service.proto` for the complete API definition.

### Key Operations

- Matrix multiplication
- Matrix inversion
- Polynomial root finding
- Linear system solving
- Eigenvalue decomposition
- SVD decomposition

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Generate gRPC code:
```bash
python -m grpc_tools.protoc -I./proto --python_out=./src/proto --grpc_python_out=./src/proto ./proto/math_service.proto
```

3. Start the service:
```bash
python -m src.server
```

## Development

Run tests:
```bash
pytest tests/
```