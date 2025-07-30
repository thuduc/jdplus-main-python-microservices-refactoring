"""Generate Python code from protobuf definitions."""

import subprocess
import sys
from pathlib import Path

def generate_proto():
    """Generate Python code from proto files."""
    proto_dir = Path(__file__).parent.parent / "proto"
    output_dir = Path(__file__).parent / "proto"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Generate Python code
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"-I{proto_dir}",
        f"--python_out={output_dir}",
        f"--grpc_python_out={output_dir}",
        str(proto_dir / "math_service.proto")
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error generating proto: {result.stderr}")
        sys.exit(1)
    
    print("Proto files generated successfully")
    
    # Create __init__.py
    (output_dir / "__init__.py").touch()

if __name__ == "__main__":
    generate_proto()