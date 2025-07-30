"""Tests for gRPC server."""

import pytest
import grpc
import numpy as np
from concurrent import futures
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Generate proto files before importing
import subprocess
result = subprocess.run([sys.executable, str(Path(__file__).parent.parent / "src" / "generate_proto.py")], capture_output=True)
if result.returncode != 0:
    raise RuntimeError(f"Failed to generate proto files: {result.stderr}")

from src.proto import math_service_pb2
from src.proto import math_service_pb2_grpc
from src.server import MathServicer


class TestMathGRPCServer:
    """Test Math gRPC server."""
    
    @pytest.fixture(scope="class")
    def grpc_server(self):
        """Create and start gRPC server for testing."""
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        math_service_pb2_grpc.add_MathServiceServicer_to_server(MathServicer(), server)
        server.add_insecure_port('[::]:0')
        port = server.add_insecure_port('[::]:0')
        server.start()
        
        yield f'localhost:{port}'
        
        server.stop(grace=None)
    
    @pytest.fixture
    def stub(self, grpc_server):
        """Create gRPC stub."""
        channel = grpc.insecure_channel(grpc_server)
        return math_service_pb2_grpc.MathServiceStub(channel)
    
    def test_multiply_matrices(self, stub):
        """Test matrix multiplication via gRPC."""
        # Create request
        request = math_service_pb2.MatrixMultiplyRequest()
        
        # Matrix A: 2x3
        request.a.data.extend([1, 2, 3, 4, 5, 6])
        request.a.rows = 2
        request.a.cols = 3
        
        # Matrix B: 3x2
        request.b.data.extend([7, 8, 9, 10, 11, 12])
        request.b.rows = 3
        request.b.cols = 2
        
        # Call service
        response = stub.MultiplyMatrices(request)
        
        # Check result
        assert response.result.rows == 2
        assert response.result.cols == 2
        result_matrix = np.array(response.result.data).reshape(2, 2)
        expected = np.array([[58, 64], [139, 154]])
        assert np.array_equal(result_matrix, expected)
    
    def test_invert_matrix(self, stub):
        """Test matrix inversion via gRPC."""
        request = math_service_pb2.MatrixInverseRequest()
        
        # 2x2 matrix
        request.matrix.data.extend([4, 7, 2, 6])
        request.matrix.rows = 2
        request.matrix.cols = 2
        
        response = stub.InvertMatrix(request)
        
        assert response.result.rows == 2
        assert response.result.cols == 2
        assert response.condition_number > 0
        
        # Verify A * A^-1 = I
        original = np.array([4, 7, 2, 6]).reshape(2, 2)
        inverse = np.array(response.result.data).reshape(2, 2)
        identity = np.dot(original, inverse)
        assert np.allclose(identity, np.eye(2))
    
    def test_find_polynomial_roots(self, stub):
        """Test polynomial root finding via gRPC."""
        request = math_service_pb2.PolynomialRootsRequest()
        
        # x^2 - 5x + 6 = 0, roots are 2 and 3
        request.polynomial.coefficients.extend([1, -5, 6])
        
        response = stub.FindPolynomialRoots(request)
        
        assert len(response.roots) == 2
        roots_real = sorted([r.real for r in response.roots])
        assert np.allclose(roots_real, [2, 3], rtol=1e-5)
    
    def test_solve_linear_system(self, stub):
        """Test linear system solving via gRPC."""
        request = math_service_pb2.LinearSolveRequest()
        
        # 2x + y = 5, x + 3y = 7
        request.a.data.extend([2, 1, 1, 3])
        request.a.rows = 2
        request.a.cols = 2
        request.b.data.extend([5, 7])
        
        response = stub.SolveLinearSystem(request)
        
        assert len(response.x.data) == 2
        solution = np.array(response.x.data)
        assert np.allclose(solution, [1.4, 2.2], rtol=1e-5)
        assert response.residual_norm < 1e-10
    
    def test_eigen_decomposition(self, stub):
        """Test eigenvalue decomposition via gRPC."""
        request = math_service_pb2.EigenDecompositionRequest()
        
        # Symmetric matrix
        request.matrix.data.extend([4, -2, -2, 1])
        request.matrix.rows = 2
        request.matrix.cols = 2
        request.compute_eigenvectors = True
        
        response = stub.ComputeEigenDecomposition(request)
        
        assert len(response.eigenvalues) == 2
        assert response.eigenvectors.rows == 2
        assert response.eigenvectors.cols == 2
        
        # Check eigenvalues
        eigenvals_real = sorted([e.real for e in response.eigenvalues])
        assert np.allclose(eigenvals_real, [0, 5], rtol=1e-5)
    
    def test_svd(self, stub):
        """Test SVD via gRPC."""
        request = math_service_pb2.SVDRequest()
        
        # 2x3 matrix
        request.matrix.data.extend([1, 2, 3, 4, 5, 6])
        request.matrix.rows = 2
        request.matrix.cols = 3
        request.full_matrices = False
        
        response = stub.ComputeSVD(request)
        
        assert response.u.rows == 2
        assert response.u.cols == 2
        assert len(response.singular_values.data) == 2
        assert response.vt.rows == 2
        assert response.vt.cols == 3
        
        # Verify reconstruction
        U = np.array(response.u.data).reshape(response.u.rows, response.u.cols)
        s = np.array(response.singular_values.data)
        Vt = np.array(response.vt.data).reshape(response.vt.rows, response.vt.cols)
        
        S = np.zeros((2, 3))
        S[:2, :2] = np.diag(s)
        reconstructed = U @ S @ Vt[:2, :]
        original = np.array([1, 2, 3, 4, 5, 6]).reshape(2, 3)
        assert np.allclose(reconstructed, original, rtol=1e-5)
    
    def test_error_handling(self, stub):
        """Test error handling in gRPC server."""
        # Invalid matrix dimensions
        request = math_service_pb2.MatrixMultiplyRequest()
        request.a.data.extend([1, 2, 3])
        request.a.rows = 2  # Wrong dimensions
        request.a.cols = 2
        request.b.data.extend([4, 5])
        request.b.rows = 2
        request.b.cols = 1
        
        with pytest.raises(grpc.RpcError) as exc_info:
            stub.MultiplyMatrices(request)
        
        assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT
        
        # Singular matrix inversion
        inv_request = math_service_pb2.MatrixInverseRequest()
        inv_request.matrix.data.extend([1, 2, 2, 4])  # Singular
        inv_request.matrix.rows = 2
        inv_request.matrix.cols = 2
        
        with pytest.raises(grpc.RpcError) as exc_info:
            stub.InvertMatrix(inv_request)
        
        assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT