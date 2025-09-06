#!/usr/bin/env python3
"""
Test runner script for all services
"""

import os
import sys
import subprocess

def run_test(test_file):
    """Run a specific test file"""
    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ Test passed!")
            print(result.stdout)
        else:
            print("❌ Test failed!")
            print(result.stdout)
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running All Service Tests")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("services") or not os.path.exists("tests"):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # List of tests to run
    tests = [
        "tests/test_diary_service.py",
        "tests/test_email_service.py"
    ]
    
    results = []
    
    for test in tests:
        if os.path.exists(test):
            success = run_test(test)
            results.append((test, success))
        else:
            print(f"⚠️  Test file not found: {test}")
            results.append((test, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Summary")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
