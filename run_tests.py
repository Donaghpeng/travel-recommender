"""
run_tests.py — Run all tests with pytest
Usage:  python run_tests.py   (requires: pip install pytest)
        python run_tests.py -v  (verbose)
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

try:
    import pytest
except ImportError:
    print("需要安装 pytest 才能运行测试")
    print("  pip install pytest")
    sys.exit(1)

# Run all tests in tests/ directory
args = sys.argv[1:] if len(sys.argv) > 1 else ["-v", "--tb=short"]
exit_code = pytest.main([os.path.join(os.path.dirname(__file__), "tests")] + args)
sys.exit(exit_code)
