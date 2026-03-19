#!/usr/bin/env python3
"""Quick test of validators."""
import os
import sys

# Set environment variables
os.environ['JIRA_URL'] = 'invalid-url'
os.environ['BRANCH_NAMING_PATTERN'] = '[invalid(regex'

from lib.config import JiraConfig, BranchConfig

print("=== Test 1: JiraConfig with invalid URL ===")
try:
    c = JiraConfig()
    print(f"FAIL: No exception raised. Got url={c.url}")
    sys.exit(1)
except ValueError as e:
    print(f"PASS: ValueError raised: {e}")

print("\n=== Test 2: BranchConfig with invalid pattern ===")
try:
    c = BranchConfig()
    print(f"FAIL: No exception raised. Got pattern={c.naming_pattern}")
    sys.exit(1)
except ValueError as e:
    print(f"PASS: ValueError raised: {e}")

print("\n=== All validator tests passed! ===")
sys.exit(0)
