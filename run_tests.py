#!/usr/bin/env python3
"""
Test runner script for the data upload endpoint tests
"""
import subprocess
import sys
import os


def run_tests():
    """Run the test suite"""
    print("Running data upload endpoint tests...")

    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_data_upload.py",
        "-v",
        "--tb=short",
        "--disable-warnings"
    ]

    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return e.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
