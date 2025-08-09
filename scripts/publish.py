#!/usr/bin/env python3
"""
PyFrame Publishing Script

This script helps with building and publishing PyFrame to PyPI.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return True if successful"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"Error: {result.stderr}")
        return False
    
    if result.stdout:
        print(result.stdout)
    return True

def check_requirements():
    """Check if required tools are installed"""
    print("🔍 Checking requirements...")
    
    required_packages = ['build', 'twine']
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is not installed")
            print(f"Install with: pip install {package}")
            return False
    
    return True

def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning build artifacts...")
    
    dirs_to_clean = ['build', 'dist', '*.egg-info']
    for pattern in dirs_to_clean:
        if '*' in pattern:
            import glob
            for path in glob.glob(pattern):
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                    print(f"Removed {path}")
        else:
            if os.path.exists(pattern):
                import shutil
                shutil.rmtree(pattern)
                print(f"Removed {pattern}")

def build_package():
    """Build the package"""
    print("📦 Building package...")
    return run_command([sys.executable, "-m", "build"])

def check_package():
    """Check the built package"""
    print("🔍 Checking package...")
    return run_command([sys.executable, "-m", "twine", "check", "dist/*"])

def upload_to_test_pypi():
    """Upload to Test PyPI"""
    print("📤 Uploading to Test PyPI...")
    return run_command([
        sys.executable, "-m", "twine", "upload", 
        "--repository", "testpypi", 
        "dist/*"
    ])

def upload_to_pypi():
    """Upload to PyPI"""
    print("📤 Uploading to PyPI...")
    return run_command([sys.executable, "-m", "twine", "upload", "dist/*"])

def main():
    """Main publishing workflow"""
    print("🚀 PyFrame Publishing Script")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("pyproject.toml"):
        print("❌ Error: pyproject.toml not found. Run this script from the project root.")
        sys.exit(1)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please install required packages and try again.")
        sys.exit(1)
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Build package only")
    print("2. Build and upload to Test PyPI")
    print("3. Build and upload to PyPI (production)")
    print("4. Clean build artifacts")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "4":
        clean_build()
        print("✅ Build artifacts cleaned!")
        return
    
    if choice not in ["1", "2", "3"]:
        print("❌ Invalid choice. Exiting.")
        sys.exit(1)
    
    # Clean previous builds
    clean_build()
    
    # Build package
    if not build_package():
        print("❌ Build failed!")
        sys.exit(1)
    
    # Check package
    if not check_package():
        print("❌ Package check failed!")
        sys.exit(1)
    
    print("✅ Package built and checked successfully!")
    
    if choice == "1":
        print("📦 Package is ready in the 'dist' directory.")
        return
    
    # Upload based on choice
    if choice == "2":
        if upload_to_test_pypi():
            print("✅ Successfully uploaded to Test PyPI!")
            print("🔗 Check your package at: https://test.pypi.org/project/pyframe/")
            print("💡 Test install with: pip install -i https://test.pypi.org/simple/ pyframe")
        else:
            print("❌ Upload to Test PyPI failed!")
            sys.exit(1)
    
    elif choice == "3":
        print("⚠️  You are about to upload to PyPI (production)!")
        confirm = input("Are you sure? This cannot be undone (y/N): ").strip().lower()
        
        if confirm != "y":
            print("❌ Upload cancelled.")
            sys.exit(1)
        
        if upload_to_pypi():
            print("🎉 Successfully uploaded to PyPI!")
            print("🔗 Check your package at: https://pypi.org/project/pyframe/")
            print("💡 Users can now install with: pip install pyframe")
        else:
            print("❌ Upload to PyPI failed!")
            sys.exit(1)

if __name__ == "__main__":
    main()
