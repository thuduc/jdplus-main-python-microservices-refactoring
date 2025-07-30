"""Matrix operations implementation."""

import numpy as np
from numba import jit
import scipy.linalg as la


def validate_matrix(data: list[float], rows: int, cols: int) -> np.ndarray:
    """Validate and reshape matrix data."""
    if len(data) != rows * cols:
        raise ValueError(f"Data length {len(data)} doesn't match dimensions {rows}x{cols}")
    
    return np.array(data).reshape(rows, cols)


def multiply_matrices(a_data: list[float], a_rows: int, a_cols: int,
                     b_data: list[float], b_rows: int, b_cols: int) -> np.ndarray:
    """Multiply two matrices."""
    a = validate_matrix(a_data, a_rows, a_cols)
    b = validate_matrix(b_data, b_rows, b_cols)
    
    if a_cols != b_rows:
        raise ValueError(f"Incompatible dimensions: ({a_rows},{a_cols}) x ({b_rows},{b_cols})")
    
    return np.dot(a, b)


def invert_matrix(data: list[float], rows: int, cols: int) -> tuple[np.ndarray, float]:
    """
    Invert a matrix and return the inverse with condition number.
    
    Returns:
        Tuple of (inverse_matrix, condition_number)
    """
    if rows != cols:
        raise ValueError("Matrix must be square for inversion")
    
    matrix = validate_matrix(data, rows, cols)
    
    # Compute condition number
    cond = np.linalg.cond(matrix)
    
    if cond > 1e15:
        raise ValueError(f"Matrix is ill-conditioned (condition number: {cond:.2e})")
    
    try:
        inv = np.linalg.inv(matrix)
        return inv, cond
    except np.linalg.LinAlgError as e:
        raise ValueError(f"Matrix inversion failed: {str(e)}")


def solve_linear_system(a_data: list[float], a_rows: int, a_cols: int,
                       b_data: list[float]) -> tuple[np.ndarray, float]:
    """
    Solve linear system Ax = b.
    
    Returns:
        Tuple of (solution_vector, residual_norm)
    """
    A = validate_matrix(a_data, a_rows, a_cols)
    b = np.array(b_data)
    
    if a_rows != len(b):
        raise ValueError(f"Incompatible dimensions: A is {a_rows}x{a_cols}, b has length {len(b)}")
    
    try:
        # Use least squares for over/under-determined systems
        x, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
        
        # Compute residual norm
        residual_norm = np.linalg.norm(A @ x - b)
        
        return x, residual_norm
    except np.linalg.LinAlgError as e:
        raise ValueError(f"Linear solve failed: {str(e)}")


def compute_eigendecomposition(data: list[float], rows: int, cols: int,
                              compute_eigenvectors: bool) -> tuple:
    """
    Compute eigenvalue decomposition.
    
    Returns:
        If compute_eigenvectors is True: (eigenvalues, eigenvectors)
        Otherwise: (eigenvalues, None)
    """
    if rows != cols:
        raise ValueError("Matrix must be square for eigendecomposition")
    
    matrix = validate_matrix(data, rows, cols)
    
    try:
        if compute_eigenvectors:
            eigenvalues, eigenvectors = np.linalg.eig(matrix)
            return eigenvalues, eigenvectors
        else:
            eigenvalues = np.linalg.eigvals(matrix)
            return eigenvalues, None
    except np.linalg.LinAlgError as e:
        raise ValueError(f"Eigendecomposition failed: {str(e)}")


def compute_svd(data: list[float], rows: int, cols: int,
                full_matrices: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute Singular Value Decomposition.
    
    Returns:
        Tuple of (U, singular_values, Vt)
    """
    matrix = validate_matrix(data, rows, cols)
    
    try:
        U, s, Vt = np.linalg.svd(matrix, full_matrices=full_matrices)
        return U, s, Vt
    except np.linalg.LinAlgError as e:
        raise ValueError(f"SVD failed: {str(e)}")


@jit(nopython=True)
def _fast_matrix_multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Numba-optimized matrix multiplication for small matrices."""
    m, k = a.shape
    k2, n = b.shape
    assert k == k2
    
    c = np.zeros((m, n))
    for i in range(m):
        for j in range(n):
            for l in range(k):
                c[i, j] += a[i, l] * b[l, j]
    return c


def fast_multiply_small(a_data: list[float], a_rows: int, a_cols: int,
                       b_data: list[float], b_rows: int, b_cols: int) -> np.ndarray:
    """Fast matrix multiplication for small matrices using Numba."""
    a = validate_matrix(a_data, a_rows, a_cols)
    b = validate_matrix(b_data, b_rows, b_cols)
    
    if a_cols != b_rows:
        raise ValueError(f"Incompatible dimensions: ({a_rows},{a_cols}) x ({b_rows},{b_cols})")
    
    # Use Numba for small matrices, NumPy for larger ones
    if a_rows * a_cols * b_cols < 1000:
        return _fast_matrix_multiply(a, b)
    else:
        return np.dot(a, b)