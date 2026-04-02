#!/usr/bin/env python3
"""Validate YAML files for syntax and style.

This script checks one or more YAML files using yamllint. Config is resolved
in priority order: --config flag, then .yamllint.yml in CWD, then .yamllint
in CWD, then yamllint's built-in 'default' preset.

Usage:
  python validate_yaml.py [FILES...] [--config CONFIG]

Arguments:
  FILES          One or more YAML file paths to validate

Options:
  --config FILE  Path to yamllint config file
  --help         Show this help message
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to path to allow imports from lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from yamllint import linter  # type: ignore
from yamllint.config import YamlLintConfig  # type: ignore

logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str]) -> YamlLintConfig:
    """Resolve and load the yamllint config.

    Priority:
        1. Explicit --config flag
        2. .yamllint.yml in CWD
        3. .yamllint in CWD
        4. Built-in 'default' preset

    Args:
        config_path: Path supplied via --config, or None.

    Returns:
        YamlLintConfig: The resolved config object.
    """
    if config_path:
        logger.info("Using yamllint config from --config flag: %s", config_path)
        return YamlLintConfig(file=config_path)

    cwd = Path.cwd()
    for candidate in (".yamllint.yml", ".yamllint"):
        candidate_path = cwd / candidate
        if candidate_path.is_file():
            logger.info("Using yamllint config found at: %s", candidate_path)
            return YamlLintConfig(file=str(candidate_path))

    logger.info("No yamllint config found; using built-in 'default' preset")
    return YamlLintConfig("extends: default")


def lint_file(file_path: str, conf: YamlLintConfig) -> bool:
    """Lint a single YAML file.

    Args:
        file_path: Path to the YAML file to validate.
        conf: The yamllint config to apply.

    Returns:
        bool: True if no problems found, False otherwise.
    """
    try:
        content = Path(file_path).read_text(encoding="utf-8")
    except OSError as e:
        print(f"✗ {file_path}: {e}")
        logger.error("Could not read file %s: %s", file_path, e)
        return False

    problems = list(linter.run(content, conf))
    if not problems:
        print(f"✓ {file_path}")
        return True

    print(f"✗ {file_path}")
    for problem in problems:
        print(
            f"  {problem.line}:{problem.column} {problem.level} {problem.message}"
        )
    return False


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for validate_yaml script.

    Args:
        argv: Argument list (defaults to sys.argv when None).

    Returns:
        int: Exit code (0 if all files valid, 1 if any invalid or on error).
    """
    parser = argparse.ArgumentParser(
        description="Validate YAML files for syntax and style"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="YAML file paths to validate",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        help="Path to yamllint config file",
    )
    args = parser.parse_args(argv)

    if not args.files:
        print("No YAML files to validate")
        return 0

    try:
        conf = load_config(args.config)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("Failed to load yamllint config: %s", e)
        print(f"✗ Could not load yamllint config: {e}")
        return 1

    all_valid = True
    for file_path in args.files:
        if not lint_file(file_path, conf):
            all_valid = False

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
