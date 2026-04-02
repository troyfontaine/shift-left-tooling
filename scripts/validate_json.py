#!/usr/bin/env python3
"""Validate JSON files for well-formedness.

This script checks one or more JSON files using the Python standard library.
No external dependencies are required.

Usage:
  python validate_json.py [FILES...]

Arguments:
  FILES    One or more JSON file paths to validate

Options:
  --help   Show this help message
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to path to allow imports from lib
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


def validate_file(file_path: str) -> bool:
    """Validate a single JSON file for well-formedness.

    Args:
        file_path: Path to the JSON file to validate.

    Returns:
        bool: True if valid JSON, False otherwise.
    """
    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except OSError as e:
        print(f"✗ {file_path}: {e}")
        logger.error("Could not read file %s: %s", file_path, e)
        return False

    try:
        json.loads(content)
        print(f"✓ {file_path}")
        return True
    except json.JSONDecodeError as e:
        print(f"✗ {file_path}: {e}")
        logger.error("Invalid JSON in %s: %s", file_path, e)
        return False


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for validate_json script.

    Args:
        argv: Argument list (defaults to sys.argv when None).

    Returns:
        int: Exit code (0 if all files valid, 1 if any invalid or on error).
    """
    parser = argparse.ArgumentParser(
        description="Validate JSON files for well-formedness"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="JSON file paths to validate",
    )
    args = parser.parse_args(argv)

    if not args.files:
        print("No JSON files to validate")
        return 0

    all_valid = True
    for file_path in args.files:
        if not validate_file(file_path):
            all_valid = False

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
