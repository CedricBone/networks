#!/usr/bin/env python3
"""
Test runner for P2P File Sharing System
Runs all tests in the tests directory
"""
import os
import sys
import unittest

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

def run_all_tests():
    """Run all test cases in the tests directory"""
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success/failure based on test results
    return result.wasSuccessful()

def run_specific_test(test_name):
    """Run a specific test file"""
    if not test_name.startswith('test_'):
        test_name = f'test_{test_name}'
    if not test_name.endswith('.py'):
        test_name = f'{test_name}.py'
    
    # Check if test file exists
    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), test_name)
    if not os.path.exists(test_file):
        print(f"Test file {test_name} not found")
        return False
    
    # Load and run the test
    module_name = test_name[:-3]  # Remove .py extension
    module = __import__(module_name)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(module)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success/failure based on test results
    return result.wasSuccessful()

if __name__ == "__main__":
    # Check if a specific test was requested
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        print(f"Running {test_name} tests...")
        success = run_specific_test(test_name)
    else:
        # Run all tests by default
        print("Running all tests...")
        success = run_all_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
