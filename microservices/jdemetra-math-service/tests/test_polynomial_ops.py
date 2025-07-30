"""Tests for polynomial operations."""

import pytest
import numpy as np
from src.core.polynomial_ops import (
    find_polynomial_roots, evaluate_polynomial, multiply_polynomials,
    add_polynomials, polynomial_derivative, polynomial_integral,
    polynomial_from_roots, polynomial_division
)


class TestPolynomialOperations:
    """Test polynomial operation functions."""
    
    def test_find_polynomial_roots(self):
        """Test finding polynomial roots."""
        # Quadratic: x^2 - 5x + 6 = 0, roots are 2 and 3
        coeffs = [1, -5, 6]
        roots = find_polynomial_roots(coeffs)
        assert len(roots) == 2
        assert np.allclose(sorted(roots.real), [2, 3], rtol=1e-5)
        
        # Linear: 2x + 4 = 0, root is -2
        coeffs_linear = [2, 4]
        roots_linear = find_polynomial_roots(coeffs_linear)
        assert len(roots_linear) == 1
        assert np.isclose(roots_linear[0], -2)
        
        # Constant polynomial has no roots
        coeffs_const = [5]
        roots_const = find_polynomial_roots(coeffs_const)
        assert len(roots_const) == 0
        
        # Empty coefficients
        with pytest.raises(ValueError, match="at least one coefficient"):
            find_polynomial_roots([])
        
        # All zeros
        with pytest.raises(ValueError, match="cannot be all zeros"):
            find_polynomial_roots([0, 0, 0])
        
        # Complex roots: x^2 + 1 = 0
        coeffs_complex = [1, 0, 1]
        roots_complex = find_polynomial_roots(coeffs_complex)
        assert len(roots_complex) == 2
        assert np.allclose(sorted(roots_complex.imag), [-1, 1], rtol=1e-5)
    
    def test_evaluate_polynomial(self):
        """Test polynomial evaluation."""
        # p(x) = 2x^3 + 3x^2 - 5x + 1
        coeffs = np.array([2, 3, -5, 1])
        
        # Evaluate at x = 2
        result = evaluate_polynomial(coeffs, 2.0)
        expected = 2*(2**3) + 3*(2**2) - 5*2 + 1  # 16 + 12 - 10 + 1 = 19
        assert np.isclose(result, expected)
        
        # Evaluate at x = 0
        result_zero = evaluate_polynomial(coeffs, 0.0)
        assert result_zero == 1.0
        
        # Evaluate at complex number
        result_complex = evaluate_polynomial(coeffs, 1+1j)
        # Manual calculation for verification
        x = 1 + 1j
        expected_complex = 2*x**3 + 3*x**2 - 5*x + 1
        assert np.isclose(result_complex, expected_complex)
    
    def test_multiply_polynomials(self):
        """Test polynomial multiplication."""
        # (x + 2) * (x - 3) = x^2 - x - 6
        p1 = [1, 2]  # x + 2
        p2 = [1, -3]  # x - 3
        
        result = multiply_polynomials(p1, p2)
        expected = [1, -1, -6]  # x^2 - x - 6
        assert np.allclose(result, expected)
        
        # Multiply by constant
        p3 = [3]  # 3
        p4 = [2, -1, 4]  # 2x^2 - x + 4
        result2 = multiply_polynomials(p3, p4)
        expected2 = [6, -3, 12]  # 6x^2 - 3x + 12
        assert np.allclose(result2, expected2)
        
        # Empty polynomial
        assert multiply_polynomials([], [1, 2]) == []
        assert multiply_polynomials([1, 2], []) == []
    
    def test_add_polynomials(self):
        """Test polynomial addition."""
        # (2x^2 + 3x + 1) + (x^2 - 2x + 4) = 3x^2 + x + 5
        p1 = [2, 3, 1]
        p2 = [1, -2, 4]
        
        result = add_polynomials(p1, p2)
        expected = [3, 1, 5]
        assert result == expected
        
        # Different degrees
        p3 = [1, 2, 3]  # x^2 + 2x + 3
        p4 = [5, 6]     # 5x + 6
        result2 = add_polynomials(p3, p4)
        expected2 = [1, 7, 9]  # x^2 + 7x + 9
        assert result2 == expected2
        
        # Adding with empty
        assert add_polynomials([], [1, 2, 3]) == [1, 2, 3]
        assert add_polynomials([1, 2, 3], []) == [1, 2, 3]
        
        # Result has leading zeros (should be removed)
        p5 = [1, 2, 3]
        p6 = [-1, -2, -3]
        result3 = add_polynomials(p5, p6)
        assert result3 == [0]  # Not empty list
    
    def test_polynomial_derivative(self):
        """Test polynomial differentiation."""
        # d/dx(3x^3 + 2x^2 - 5x + 7) = 9x^2 + 4x - 5
        coeffs = [3, 2, -5, 7]
        deriv = polynomial_derivative(coeffs)
        expected = [9, 4, -5]
        assert deriv == expected
        
        # Constant polynomial
        const_coeffs = [5]
        const_deriv = polynomial_derivative(const_coeffs)
        assert const_deriv == [0]
        
        # Linear polynomial
        linear_coeffs = [2, 3]  # 2x + 3
        linear_deriv = polynomial_derivative(linear_coeffs)
        assert linear_deriv == [2]  # 2
        
        # Empty polynomial
        assert polynomial_derivative([]) == [0]
    
    def test_polynomial_integral(self):
        """Test polynomial integration."""
        # ∫(3x^2 + 2x - 1)dx = x^3 + x^2 - x + C
        coeffs = [3, 2, -1]
        integral = polynomial_integral(coeffs, constant=5)
        expected = [1, 1, -1, 5]  # x^3 + x^2 - x + 5
        assert integral == expected
        
        # Without constant
        integral_no_const = polynomial_integral(coeffs)
        expected_no_const = [1, 1, -1, 0]
        assert integral_no_const == expected_no_const
        
        # Constant polynomial
        const_integral = polynomial_integral([5], constant=2)
        assert const_integral == [5, 2]  # 5x + 2
        
        # Empty polynomial
        assert polynomial_integral([]) == [0]
    
    def test_polynomial_from_roots(self):
        """Test constructing polynomial from roots."""
        # Roots 2 and 3 give (x-2)(x-3) = x^2 - 5x + 6
        roots = [2, 3]
        poly = polynomial_from_roots(roots)
        expected = [1, -5, 6]
        assert np.allclose(poly, expected)
        
        # Single root
        single_root = [4]
        single_poly = polynomial_from_roots(single_root)
        assert single_poly == [1, -4]  # x - 4
        
        # No roots gives constant polynomial
        no_roots = []
        no_roots_poly = polynomial_from_roots(no_roots)
        assert no_roots_poly == [1]
        
        # Complex conjugate roots
        complex_roots = [1+2j, 1-2j]
        complex_poly = polynomial_from_roots(complex_roots)
        # (x - (1+2i))(x - (1-2i)) = x^2 - 2x + 5
        expected_complex = [1, -2, 5]
        assert np.allclose(complex_poly, expected_complex, rtol=1e-10)
    
    def test_polynomial_division(self):
        """Test polynomial division."""
        # (x^3 + 2x^2 - 5x - 6) / (x - 2) = x^2 + 4x + 3, remainder 0
        dividend = [1, 2, -5, -6]
        divisor = [1, -2]
        
        quotient, remainder = polynomial_division(dividend, divisor)
        expected_quotient = [1, 4, 3]
        expected_remainder = [0]
        
        assert np.allclose(quotient, expected_quotient)
        assert np.allclose(remainder, expected_remainder, atol=1e-10)
        
        # Division with remainder
        dividend2 = [1, 0, -4]  # x^2 - 4
        divisor2 = [1, -1]  # x - 1
        quotient2, remainder2 = polynomial_division(dividend2, divisor2)
        # x^2 - 4 = (x - 1)(x + 1) - 3
        assert np.allclose(quotient2, [1, 1])
        assert np.allclose(remainder2, [-3])
        
        # Division by zero polynomial
        with pytest.raises(ValueError, match="Division by zero"):
            polynomial_division([1, 2, 3], [0, 0])
        
        # Dividend smaller than divisor
        small_dividend = [1, 2]  # x + 2
        large_divisor = [1, 2, 3]  # x^2 + 2x + 3
        q_small, r_small = polynomial_division(small_dividend, large_divisor)
        assert q_small == [0]
        assert r_small == [1, 2]
    
    def test_polynomial_operations_integration(self):
        """Test integration of multiple polynomial operations."""
        # Start with roots
        roots = [1, -2, 3]
        poly = polynomial_from_roots(roots)
        
        # Verify roots
        found_roots = find_polynomial_roots(poly)
        assert len(found_roots) == 3
        assert np.allclose(sorted(found_roots.real), sorted(roots), rtol=1e-5)
        
        # Take derivative
        deriv = polynomial_derivative(poly)
        
        # Integrate back (without constant)
        integral = polynomial_integral(deriv)
        
        # Should get original polynomial back (up to constant)
        # Compare ratios since constant term might differ
        ratio = poly[0] / integral[0]
        scaled_integral = [coeff * ratio for coeff in integral[:-1]]
        assert np.allclose(scaled_integral, poly, rtol=1e-10)