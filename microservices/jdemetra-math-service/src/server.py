"""gRPC server for mathematical operations service."""

import grpc
from concurrent import futures
import logging
import signal
import sys
from pathlib import Path

# Add proto directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import after path modification
from proto import math_service_pb2
from proto import math_service_pb2_grpc
from core.matrix_ops import (
    multiply_matrices, invert_matrix, solve_linear_system,
    compute_eigendecomposition, compute_svd
)
from core.polynomial_ops import find_polynomial_roots

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MathServicer(math_service_pb2_grpc.MathServiceServicer):
    """Implementation of the Math service."""
    
    def MultiplyMatrices(self, request, context):
        """Multiply two matrices."""
        try:
            result = multiply_matrices(
                request.a.data, request.a.rows, request.a.cols,
                request.b.data, request.b.rows, request.b.cols
            )
            
            response = math_service_pb2.MatrixMultiplyResponse()
            response.result.data.extend(result.flatten().tolist())
            response.result.rows = result.shape[0]
            response.result.cols = result.shape[1]
            
            return response
            
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return math_service_pb2.MatrixMultiplyResponse()
        except Exception as e:
            logger.error(f"Error in MultiplyMatrices: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return math_service_pb2.MatrixMultiplyResponse()
    
    def InvertMatrix(self, request, context):
        """Invert a matrix."""
        try:
            inv, cond = invert_matrix(
                request.matrix.data, request.matrix.rows, request.matrix.cols
            )
            
            response = math_service_pb2.MatrixInverseResponse()
            response.result.data.extend(inv.flatten().tolist())
            response.result.rows = inv.shape[0]
            response.result.cols = inv.shape[1]
            response.condition_number = cond
            
            return response
            
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return math_service_pb2.MatrixInverseResponse()
        except Exception as e:
            logger.error(f"Error in InvertMatrix: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return math_service_pb2.MatrixInverseResponse()
    
    def FindPolynomialRoots(self, request, context):
        """Find roots of a polynomial."""
        try:
            roots = find_polynomial_roots(list(request.polynomial.coefficients))
            
            response = math_service_pb2.PolynomialRootsResponse()
            for root in roots:
                complex_root = response.roots.add()
                complex_root.real = root.real
                complex_root.imag = root.imag
            
            return response
            
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return math_service_pb2.PolynomialRootsResponse()
        except Exception as e:
            logger.error(f"Error in FindPolynomialRoots: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return math_service_pb2.PolynomialRootsResponse()
    
    def SolveLinearSystem(self, request, context):
        """Solve linear system Ax = b."""
        try:
            solution, residual = solve_linear_system(
                request.a.data, request.a.rows, request.a.cols,
                list(request.b.data)
            )
            
            response = math_service_pb2.LinearSolveResponse()
            response.x.data.extend(solution.tolist())
            response.residual_norm = residual
            
            return response
            
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return math_service_pb2.LinearSolveResponse()
        except Exception as e:
            logger.error(f"Error in SolveLinearSystem: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return math_service_pb2.LinearSolveResponse()
    
    def ComputeEigenDecomposition(self, request, context):
        """Compute eigenvalue decomposition."""
        try:
            eigenvalues, eigenvectors = compute_eigendecomposition(
                request.matrix.data, request.matrix.rows, request.matrix.cols,
                request.compute_eigenvectors
            )
            
            response = math_service_pb2.EigenDecompositionResponse()
            
            # Add eigenvalues
            for eigenval in eigenvalues:
                complex_eigen = response.eigenvalues.add()
                if isinstance(eigenval, complex):
                    complex_eigen.real = eigenval.real
                    complex_eigen.imag = eigenval.imag
                else:
                    complex_eigen.real = float(eigenval)
                    complex_eigen.imag = 0.0
            
            # Add eigenvectors if computed
            if eigenvectors is not None:
                response.eigenvectors.data.extend(eigenvectors.flatten().tolist())
                response.eigenvectors.rows = eigenvectors.shape[0]
                response.eigenvectors.cols = eigenvectors.shape[1]
            
            return response
            
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return math_service_pb2.EigenDecompositionResponse()
        except Exception as e:
            logger.error(f"Error in ComputeEigenDecomposition: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return math_service_pb2.EigenDecompositionResponse()
    
    def ComputeSVD(self, request, context):
        """Compute Singular Value Decomposition."""
        try:
            U, s, Vt = compute_svd(
                request.matrix.data, request.matrix.rows, request.matrix.cols,
                request.full_matrices
            )
            
            response = math_service_pb2.SVDResponse()
            
            # Add U matrix
            response.u.data.extend(U.flatten().tolist())
            response.u.rows = U.shape[0]
            response.u.cols = U.shape[1]
            
            # Add singular values
            response.singular_values.data.extend(s.tolist())
            
            # Add Vt matrix
            response.vt.data.extend(Vt.flatten().tolist())
            response.vt.rows = Vt.shape[0]
            response.vt.cols = Vt.shape[1]
            
            return response
            
        except ValueError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return math_service_pb2.SVDResponse()
        except Exception as e:
            logger.error(f"Error in ComputeSVD: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return math_service_pb2.SVDResponse()


def serve():
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    math_service_pb2_grpc.add_MathServiceServicer_to_server(MathServicer(), server)
    
    # Listen on port 50051
    port = '50051'
    server.add_insecure_port(f'[::]:{port}')
    
    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        logger.info("Shutting down server...")
        server.stop(grace=5)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server.start()
    logger.info(f"Math service started on port {port}")
    
    # Keep the server running
    server.wait_for_termination()


if __name__ == '__main__':
    # First generate the proto files
    import subprocess
    logger.info("Generating proto files...")
    result = subprocess.run([sys.executable, "src/generate_proto.py"], capture_output=True)
    if result.returncode != 0:
        logger.error(f"Failed to generate proto files: {result.stderr}")
        sys.exit(1)
    
    # Then start the server
    serve()