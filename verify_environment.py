#!/usr/bin/env python3
"""
Environment Verification Tool
=============================
Before running the full installation, verify your environment is ready.

Usage:
    python verify_environment.py
    
This will check:
- Python version
- Conda installation and PATH
- Disk space
- Required capabilities
- Common issues

Then it prints a simple PASS/FAIL verdict you can share with support.
"""

import os
import sys
import platform
import subprocess
import shutil
import json
from pathlib import Path


class EnvironmentVerifier:
    """Check if environment is ready for installation."""
    
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
        self.results = {}
    
    def verify_python_version(self):
        """Check Python version is 3.8+"""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        print(f"\n📦 Python Version: {version_str}... ", end="", flush=True)
        
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("❌ FAILED")
            self.checks_failed.append(f"Python {version_str} (need 3.8+)")
            return False
        
        if version.minor >= 13:
            print(f"⚠️  WARNING")
            self.warnings.append(f"Python 3.13+ may have compatibility issues (current: {version_str})")
        else:
            print("✓ OK")
        
        self.checks_passed.append(f"Python {version_str}")
        self.results['python_version'] = version_str
        return True
    
    def verify_platform(self):
        """Check OS compatibility"""
        os_name = platform.system()
        print(f"\n🖥️  Operating System: {os_name}... ", end="", flush=True)
        
        if os_name not in ["Windows", "Linux", "Darwin"]:
            print("❌ UNSUPPORTED")
            self.checks_failed.append(f"OS {os_name} not supported")
            return False
        
        if os_name == "Darwin":
            os_name = "macOS"
        
        print("✓ OK")
        self.checks_passed.append(f"{os_name}")
        self.results['os'] = os_name
        return True
    
    def verify_conda(self):
        """Check if Conda/Miniconda is available"""
        print(f"\n📦 Conda Installation: ", end="", flush=True)
        
        # Check if conda is in PATH
        conda_path = shutil.which("conda")
        
        if conda_path:
            print(f"✓ FOUND")
            # Get version
            try:
                result = subprocess.run(["conda", "--version"], capture_output=True, text=True, timeout=5)
                version = result.stdout.strip()
                print(f"   └─ {conda_path}")
                print(f"   └─ {version}")
                self.checks_passed.append(f"Conda (in PATH)")
                self.results['conda'] = {"status": "in_path", "path": conda_path, "version": version}
                return True
            except Exception as e:
                print(f"⚠️  Found but version check failed")
                self.warnings.append(f"Conda found at {conda_path} but version check failed: {e}")
                self.results['conda'] = {"status": "found_but_version_failed", "path": conda_path}
                return True
        
        # Check common installation locations
        common_paths = [
            os.path.expanduser("~/miniconda3"),
            os.path.expanduser("~/Miniconda3"),
            os.path.expanduser("~/anaconda3"),
            os.path.expanduser("~/Anaconda3"),
            "C:\\miniconda3",
            "C:\\Miniconda3",
            "C:\\anaconda3",
            "C:\\Anaconda3",
            os.path.expanduser("~/opt/miniconda3"),
            os.path.expanduser("~/opt/anaconda3"),
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                print(f"⚠️  INSTALLED BUT NOT IN PATH")
                print(f"   └─ Found at: {path}")
                print(f"   └─ Fix: Restart terminal or run 'python fix_conda_path.py'")
                self.warnings.append(
                    f"Conda installed at {path} but NOT in PATH. "
                    f"Restart terminal or run: python fix_conda_path.py"
                )
                self.results['conda'] = {"status": "installed_not_in_path", "path": path}
                return True
        
        # Not found
        print("❌ NOT FOUND")
        print(f"   └─ Miniconda not detected on this system")
        print(f"   └─ Will use Python venv instead (fallback)")
        self.checks_failed.append("Conda not found (will use venv instead)")
        self.results['conda'] = {"status": "not_found"}
        return False
    
    def verify_pip(self):
        """Check if pip is available"""
        print(f"\n📦 Pip (Package Manager): ", end="", flush=True)
        
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✓ OK")
                version = result.stdout.strip().split()[1]
                self.checks_passed.append(f"Pip {version}")
                self.results['pip'] = {"status": "ok", "version": version}
                return True
        except Exception:
            pass
        
        print("❌ FAILED")
        self.checks_failed.append("Pip not found")
        self.results['pip'] = {"status": "not_found"}
        return False
    
    def verify_disk_space(self):
        """Check available disk space"""
        print(f"\n💾 Disk Space: ", end="", flush=True)
        
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_gb = free / (1024**3)
            
            if free_gb < 5:
                print(f"❌ LOW ({free_gb:.1f}GB)")
                self.checks_failed.append(f"Only {free_gb:.1f}GB free (need 5GB+)")
                self.results['disk_space'] = {"status": "low", "free_gb": free_gb}
                return False
            elif free_gb < 10:
                print(f"⚠️  LOW ({free_gb:.1f}GB)")
                self.warnings.append(f"Only {free_gb:.1f}GB free (recommended 10GB+)")
                self.results['disk_space'] = {"status": "marginal", "free_gb": free_gb}
                return True
            else:
                print(f"✓ OK ({free_gb:.1f}GB free)")
                self.checks_passed.append(f"{free_gb:.1f}GB disk space")
                self.results['disk_space'] = {"status": "ok", "free_gb": free_gb}
                return True
        except Exception as e:
            print(f"⚠️  Could not check: {e}")
            self.warnings.append(f"Could not check disk space: {e}")
            return True
    
    def verify_internet(self):
        """Check internet connectivity"""
        print(f"\n🌐 Internet Connectivity: ", end="", flush=True)
        
        try:
            import urllib.request
            urllib.request.urlopen("https://pypi.org", timeout=3)
            print("✓ OK")
            self.checks_passed.append("Internet connection")
            self.results['internet'] = {"status": "ok"}
            return True
        except Exception:
            print("❌ NO CONNECTION")
            self.checks_failed.append("No internet connection (needed for pip)")
            self.results['internet'] = {"status": "no_connection"}
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        
        if self.checks_passed:
            print("\n✓ PASSED CHECKS:")
            for check in self.checks_passed:
                print(f"  ✓ {check}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
        
        if self.checks_failed:
            print("\n❌ FAILED CHECKS:")
            for check in self.checks_failed:
                print(f"  ❌ {check}")
        
        print("\n" + "="*60)
        
        # Final verdict
        if not self.checks_failed:
            print("✨ VERDICT: PASS - Environment ready for installation! ✨")
            print("="*60)
            print("\nNext step:")
            print("  python auto_setup.py")
            return True
        else:
            print("❌ VERDICT: FAIL - Please fix issues above")
            print("="*60)
            print("\nCommon fixes:")
            
            if "Conda not found" in self.checks_failed[0]:
                print("  • Install Miniconda: https://docs.conda.io/en/latest/miniconda.html")
                print("  • Or use venv: python -m venv myenv")
            
            if "No internet" in str(self.checks_failed):
                print("  • Check your internet connection")
                print("  • If behind proxy, configure pip")
            
            if any("only" in f.lower() for f in self.checks_failed):
                print("  • Delete some files to free disk space")
                print("  • Or use external drive")
            
            if any("python" in f.lower() for f in self.checks_failed):
                print("  • Install Python 3.8+: https://www.python.org/downloads/")
            
            return False
    
    def save_results(self):
        """Save results to JSON file"""
        output_file = "environment_verification.json"
        with open(output_file, "w") as f:
            json.dump({
                "passed": self.checks_passed,
                "failed": self.checks_failed,
                "warnings": self.warnings,
                "details": self.results,
                "verdict": "PASS" if not self.checks_failed else "FAIL"
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: {output_file}")


def main():
    """Run verification"""
    print("\n" + "="*60)
    print("🔍 CRAFTBOT ENVIRONMENT VERIFICATION")
    print("="*60)
    print("\nChecking if your system is ready for installation...")
    
    verifier = EnvironmentVerifier()
    
    # Run all checks
    verifier.verify_python_version()
    verifier.verify_platform()
    verifier.verify_conda()
    verifier.verify_pip()
    verifier.verify_disk_space()
    verifier.verify_internet()
    
    # Print summary
    success = verifier.print_summary()
    
    # Save results
    verifier.save_results()
    
    # Return appropriate exit code
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
