#!/usr/bin/env python3
"""Validate branch name follows naming conventions.

This script checks if a branch name follows the configured naming pattern.
The pattern defaults to Jira ticket format (PROJ-123) but is configurable.

Usage:
  python validate_branch_naming.py [BRANCH_NAME]

Arguments:
  BRANCH_NAME    The branch name to validate (defaults to current branch)

Options:
  --pattern PATTERN    Override the naming pattern
  --help               Show this help message

Environment Variables:
  BRANCH_NAMING_PATTERN    Regex pattern for branch naming (default: ^[A-Z]+-\\d+)
"""

import argparse
import logging
import re
import sys

from lib.config import get_config
from lib.git_utils import GitProviderError, get_current_branch

logger = logging.getLogger(__name__)


def validate_branch_naming(branch_name: str, pattern: str) -> bool:
    """Validate branch name against pattern.

    Args:
        branch_name: The branch name to validate.
        pattern: The regex pattern to validate against.

    Returns:
        bool: True if branch name matches pattern, False otherwise.
    """
    try:
        # Check if pattern matches
        if re.match(pattern, branch_name):
            logger.info(
                "Branch name '%s' matches pattern '%s'", branch_name, pattern
            )
            return True
        else:
            logger.warning(
                "Branch name '%s' does not match pattern '%s'",
                branch_name,
                pattern,
            )
            return False
    except re.error as e:
        logger.error("Invalid regex pattern: %s", e)
        return False


def main() -> int:
    """Main entry point for validate_branch_naming script.

    Returns:
        int: Exit code (0 for valid, 1 for invalid).
    """
    parser = argparse.ArgumentParser(
        description="Validate branch name follows naming convention"
    )
    parser.add_argument(
        "branch_name",
        nargs="?",
        help="The branch name to validate (defaults to current branch)",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        help="Override the naming pattern",
    )
    args = parser.parse_args()

    # Get branch name
    if args.branch_name:
        branch_name = args.branch_name
    else:
        try:
            branch_name = get_current_branch()
        except GitProviderError as e:
            logger.error("Could not determine current branch: %s", e)
            return 1

    # Get naming pattern
    if args.pattern:
        pattern = args.pattern
    else:
        config = get_config()
        pattern = config.branch.naming_pattern

    logger.info("Validating branch: %s", branch_name)
    logger.info("Pattern: %s", pattern)

    # Validate branch name
    if validate_branch_naming(branch_name, pattern):
        print(f"✓ Branch name '{branch_name}' is valid")
        return 0
    else:
        print(
            f"✗ Branch name '{branch_name}' does not match the required pattern:\n"
            f"  Pattern: {pattern}\n"
            f"  Example: project-123-feature-description"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
