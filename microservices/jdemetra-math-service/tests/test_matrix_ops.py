"""Tests for matrix operations."""

import pytest
import numpy as np
from src.core.matrix_ops import (
    validate_matrix, multiply_matrices, invert_matrix,
    solve_linear_system, compute_eigendecomposition, compute_svd,
    fast_multiply_small
)


class TestMatrixOperations:
    """Test matrix operation functions."""
    
    def test_validate_matrix(self):
        """Test matrix validation."""
        # Valid case
        data = [1, 2, 3, 4, 5, 6]
        matrix = validate_matrix(data, 2, 3)
        assert matrix.shape == (2, 3)
        assert np.array_equal(matrix, np.array([[1, 2, 3], [4, 5, 6]]))
        
        # Invalid case
        with pytest.raises(ValueError, match="doesn't match dimensions"):
            validate_matrix([1, 2, 3], 2, 3)
    
    def test_multiply_matrices(self):
        """Test matrix multiplication."""
        # 2x3 * 3x2 = 2x2
        a_data = [1, 2, 3, 4, 5, 6]  # [[1,2,3], [4,5,6]]
        b_data = [7, 8, 9, 10, 11, 12]  # [[7,8], [9,10], [11,12]]
        
        result = multiply_matrices(a_data, 2, 3, b_data, 3, 2)
        expected = np.array([[58, 64], [139, 154]])
        assert np.array_equal(result, expected)
        
        # Incompatible dimensions
        with pytest.raises(ValueError, match="Incompatible dimensions"):
            multiply_matrices(a_data, 2, 3, b_data, 2, 2)
    
    def test_invert_matrix(self):
        """Test matrix inversion."""
        # Invertible matrix
        data = [4, 7, 2, 6]  # [[4,7], [2,6]]
        inv, cond = invert_matrix(data, 2, 2)
        
        # Check that A * A^-1 = I
        original = np.array(data).reshape(2, 2)
        identity = np.dot(original, inv)
        assert np.allclose(identity, np.eye(2))
        assert cond > 0
        
        # Non-square matrix
        with pytest.raises(ValueError, match="must be square"):
            invert_matrix([1, 2, 3, 4, 5, 6], 2, 3)
        
        # Singular matrix
        singular_data = [1, 2, 2, 4]  # [[1,2], [2,4]]
        with pytest.raises(ValueError):
            invert_matrix(singular_data, 2, 2)
    
    def test_solve_linear_system(self):
        """Test linear system solving."""
        # Simple system: 2x + y = 5, x + 3y = 7
        a_data = [2, 1, 1, 3]  # [[2,1], [1,3]]
        b_data = [5, 7]
        
        x, residual = solve_linear_system(a_data, 2, 2, b_data)
        
        # Solution should be approximately [1.4, 2.2]
        assert np.allclose(x, [1.4, 2.2], rtol=1e-5)
        assert residual < 1e-10
        
        # Over-determined system (least squares)
        a_data_od = [1, 1, 1, 2, 1, 3]  # [[1,1], [1,2], [1,3]]
        b_data_od = [2, 3, 4]
        
        x_od, residual_od = solve_linear_system(a_data_od, 3, 2, b_data_od)
        assert len(x_od) == 2
        assert residual_od >= 0
        
        # Incompatible dimensions
        with pytest.raises(ValueError, match="Incompatible dimensions"):
            solve_linear_system(a_data, 2, 2, [1, 2, 3])
    
    def test_eigendecomposition(self):
        """Test eigenvalue decomposition."""
        # Symmetric matrix with known eigenvalues
        data = [4, -2, -2, 1]  # [[4,-2], [-2,1]]
        
        # Test without eigenvectors
        eigenvalues, eigenvectors = compute_eigendecomposition(data, 2, 2, False)
        assert eigenvectors is None
        assert len(eigenvalues) == 2
        # Eigenvalues should be approximately 5 and 0
        expected_eigenvalues = [5, 0]
        assert np.allclose(sorted(eigenvalues.real), sorted(expected_eigenvalues), rtol=1e-5)
        
        # Test with eigenvectors
        eigenvalues2, eigenvectors2 = compute_eigendecomposition(data, 2, 2, True)
        assert eigenvectors2 is not None
        assert eigenvectors2.shape == (2, 2)
        
        # Verify A*v = λ*v for each eigenpair
        A = np.array(data).reshape(2, 2)
        for i in range(2):
            v = eigenvectors2[:, i]
            λ = eigenvalues2[i]
            assert np.allclose(A @ v, λ * v, rtol=1e-5)
        
        # Non-square matrix
        with pytest.raises(ValueError, match="must be square"):
            compute_eigendecomposition([1, 2, 3, 4, 5, 6], 2, 3, False)
    
    def test_svd(self):
        """Test Singular Value Decomposition."""
        # Test matrix
        data = [1, 2, 3, 4, 5, 6]  # [[1,2,3], [4,5,6]]
        
        # Full matrices
        U, s, Vt = compute_svd(data, 2, 3, True)
        assert U.shape == (2, 2)
        assert len(s) == 2
        assert Vt.shape == (3, 3)
        
        # Verify A = U * S * Vt
        S = np.zeros((2, 3))
        S[:2, :2] = np.diag(s)
        reconstructed = U @ S @ Vt
        original = np.array(data).reshape(2, 3)
        assert np.allclose(reconstructed, original)
        
        # Reduced matrices
        U_r, s_r, Vt_r = compute_svd(data, 2, 3, False)
        assert U_r.shape == (2, 2)
        assert len(s_r) == 2
        assert Vt_r.shape == (2, 3)
    
    def test_fast_multiply_small(self):
        """Test fast multiplication for small matrices."""
        # Small matrices
        a_data = [1, 2, 3, 4]  # [[1,2], [3,4]]
        b_data = [5, 6, 7, 8]  # [[5,6], [7,8]]
        
        result = fast_multiply_small(a_data, 2, 2, b_data, 2, 2)
        expected = np.array([[19, 22], [43, 50]])
        assert np.array_equal(result, expected)
        
        # Should work for larger matrices too (falls back to NumPy)
        large_a = list(range(100))
        large_b = list(range(100))
        result_large = fast_multiply_small(large_a, 10, 10, large_b, 10, 10)
        assert result_large.shape == (10, 10)
    
    def test_edge_cases(self):
        """Test edge cases."""
        # 1x1 matrix
        data_1x1 = [5.0]
        inv, cond = invert_matrix(data_1x1, 1, 1)
        assert inv[0, 0] == 0.2  # 1/5
        
        # Identity matrix
        identity_data = [1, 0, 0, 1]
        inv_i, cond_i = invert_matrix(identity_data, 2, 2)
        assert np.allclose(inv_i, np.eye(2))
        assert cond_i == 1.0
        
        # Zero matrix (should fail)
        zero_data = [0, 0, 0, 0]
        with pytest.raises(ValueError):
            invert_matrix(zero_data, 2, 2)