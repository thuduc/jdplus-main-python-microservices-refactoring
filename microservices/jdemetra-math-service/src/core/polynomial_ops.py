"""Polynomial operations implementation."""

import numpy as np
from numba import jit
from typing import List, Tuple, Union


def find_polynomial_roots(coefficients: List[float]) -> np.ndarray:
    """
    Find roots of a polynomial.
    
    Args:
        coefficients: Polynomial coefficients from highest to lowest degree
        
    Returns:
        Array of complex roots
    """
    if not coefficients:
        raise ValueError("Polynomial must have at least one coefficient")
    
    # Remove leading zeros
    coeffs = np.array(coefficients)
    nonzero_idx = np.nonzero(coeffs)[0]
    
    if len(nonzero_idx) == 0:
        raise ValueError("Polynomial cannot be all zeros")
    
    coeffs = coeffs[nonzero_idx[0]:]
    
    # Handle special cases
    if len(coeffs) == 1:
        return np.array([])  # Constant polynomial has no roots
    
    if len(coeffs) == 2:
        # Linear polynomial: ax + b = 0 => x = -b/a
        return np.array([-coeffs[1] / coeffs[0]])
    
    # Use numpy for general case
    try:
        roots = np.roots(coeffs)
        return roots
    except Exception as e:
        raise ValueError(f"Failed to find polynomial roots: {str(e)}")


@jit(nopython=True)
def evaluate_polynomial(coeffs: np.ndarray, x: Union[float, complex]) -> Union[float, complex]:
    """
    Evaluate polynomial at a given point using Horner's method.
    
    Args:
        coeffs: Polynomial coefficients from highest to lowest degree
        x: Point at which to evaluate
        
    Returns:
        Polynomial value at x
    """
    result = coeffs[0]
    for i in range(1, len(coeffs)):
        result = result * x + coeffs[i]
    return result


def multiply_polynomials(p1: List[float], p2: List[float]) -> List[float]:
    """
    Multiply two polynomials.
    
    Args:
        p1, p2: Polynomial coefficients from highest to lowest degree
        
    Returns:
        Product polynomial coefficients
    """
    if not p1 or not p2:
        return []
    
    # Convert to numpy arrays
    a = np.array(p1)
    b = np.array(p2)
    
    # Use convolution for polynomial multiplication
    result = np.convolve(a, b)
    
    return result.tolist()


def add_polynomials(p1: List[float], p2: List[float]) -> List[float]:
    """
    Add two polynomials.
    
    Args:
        p1, p2: Polynomial coefficients from highest to lowest degree
        
    Returns:
        Sum polynomial coefficients
    """
    if not p1:
        return p2
    if not p2:
        return p1
    
    # Pad shorter polynomial with zeros at the beginning
    if len(p1) < len(p2):
        p1 = [0] * (len(p2) - len(p1)) + p1
    elif len(p2) < len(p1):
        p2 = [0] * (len(p1) - len(p2)) + p2
    
    # Add corresponding coefficients
    result = [a + b for a, b in zip(p1, p2)]
    
    # Remove leading zeros
    while result and abs(result[0]) < 1e-14:
        result.pop(0)
    
    return result if result else [0]


def polynomial_derivative(coeffs: List[float]) -> List[float]:
    """
    Compute polynomial derivative.
    
    Args:
        coeffs: Polynomial coefficients from highest to lowest degree
        
    Returns:
        Derivative polynomial coefficients
    """
    if not coeffs or len(coeffs) == 1:
        return [0]
    
    # Derivative of a_n * x^n is n * a_n * x^(n-1)
    n = len(coeffs) - 1
    result = []
    
    for i, coeff in enumerate(coeffs[:-1]):
        power = n - i
        result.append(coeff * power)
    
    return result


def polynomial_integral(coeffs: List[float], constant: float = 0) -> List[float]:
    """
    Compute polynomial integral.
    
    Args:
        coeffs: Polynomial coefficients from highest to lowest degree
        constant: Integration constant
        
    Returns:
        Integral polynomial coefficients
    """
    if not coeffs:
        return [constant] if constant != 0 else [0]
    
    # Integral of a_n * x^n is a_n / (n+1) * x^(n+1)
    n = len(coeffs) - 1
    result = []
    
    for i, coeff in enumerate(coeffs):
        power = n - i + 1
        result.append(coeff / power)
    
    result.append(constant)
    
    return result


def polynomial_from_roots(roots: List[complex]) -> List[float]:
    """
    Construct polynomial from its roots.
    
    Args:
        roots: List of polynomial roots
        
    Returns:
        Polynomial coefficients (may be complex if roots are complex)
    """
    if not roots:
        return [1]
    
    # Start with (x - r0)
    poly = [1, -roots[0]]
    
    # Multiply by (x - ri) for each additional root
    for root in roots[1:]:
        poly = multiply_polynomials(poly, [1, -root])
    
    # Convert to real if all imaginary parts are negligible
    poly_array = np.array(poly)
    if np.allclose(poly_array.imag, 0):
        return poly_array.real.tolist()
    else:
        return poly  # Keep as complex


def polynomial_division(dividend: List[float], divisor: List[float]) -> Tuple[List[float], List[float]]:
    """
    Polynomial division.
    
    Args:
        dividend: Dividend polynomial coefficients
        divisor: Divisor polynomial coefficients
        
    Returns:
        Tuple of (quotient, remainder) polynomial coefficients
    """
    if not divisor or all(c == 0 for c in divisor):
        raise ValueError("Division by zero polynomial")
    
    # Convert to numpy for easier manipulation
    dividend = np.array(dividend)
    divisor = np.array(divisor)
    
    # Remove leading zeros
    dividend = np.trim_zeros(dividend, 'f')
    divisor = np.trim_zeros(divisor, 'f')
    
    if len(dividend) < len(divisor):
        return [0], dividend.tolist()
    
    quotient, remainder = np.polydiv(dividend, divisor)
    
    return quotient.tolist(), remainder.tolist()