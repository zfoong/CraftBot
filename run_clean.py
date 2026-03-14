#!/usr/bin/env python3
"""
Clean CraftBot launcher - suppresses dependency warnings
Use: python run_clean.py [options]
"""
import os
import sys
import subprocess

# Set environment to suppress urllib3/chardet warnings globally
os.environ['PYTHONWARNINGS'] = 'ignore::DeprecationWarning,ignore::PendingDeprecationWarning'

# Pass all arguments to run.py
result = subprocess.run([sys.executable, 'run.py'] + sys.argv[1:])
sys.exit(result.returncode)
