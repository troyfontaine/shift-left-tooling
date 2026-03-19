#!/usr/bin/env python3
"""Validate a branch name against Jira and GitHub patterns.

This script checks if a provided branch name matches either:
- A Jira ticket pattern (e.g., PROJ-123)
- A GitHub issue pattern (e.g., gh123, GH-456)

And optionally verifies the ticket/issue exists via API.

Usage:
  python validate_branch_name.py BRANCH_NAME [--check-exists]

Arguments:
  BRANCH_NAME    The branch name to validate

Options:
  --check-exists    Verify ticket/issue exists via API
  --help            Show this help message
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path to allow imports from lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.git_utils import (
    GitProviderError,
    extract_owner_repo,
    get_git_origin,
)
from lib.github_provider import GitHubProvider, GitHubProviderError
from lib.jira_provider import JiraProvider, JiraProviderError

logger = logging.getLogger(__name__)


def validate_jira_pattern(branch_name: str) -> Optional[str]:
    """Check if branch name contains valid Jira ticket pattern.

    Args:
        branch_name: The branch name to validate.

    Returns:
        Optional[str]: The Jira ticket ID if found, None otherwise.
    """
    match = re.search(r"\b([A-Z][A-Z0-9]*-\d+)\b", branch_name)
    if match:
        return match.group(1)
    return None


def validate_github_pattern(branch_name: str) -> Optional[str]:
    """Check if branch name contains GitHub issue pattern.

    Supports patterns like 'gh123', 'GH456', 'gh-789', 'GH-123'.
    When 'gh-' variant (with dash) is detected, logs a note that Jira will not be checked.

    Args:
        branch_name: The branch name to validate.

    Returns:
        Optional[str]: The issue number if found, None otherwise.
    """
    match = re.search(r"[Gg][Hh][-]?(\d+)", branch_name)
    if match:
        issue_number = match.group(1)
        # Check if the variant with dash was used (e.g., 'gh-123')
        if re.search(r"[Gg][Hh]-(\d+)", branch_name):
            logger.info(
                "Detected 'gh-' variant in branch name; Jira checking skipped"
            )
        return issue_number
    return None


def check_jira_ticket_exists(ticket_key: str) -> bool:
    """Check if Jira ticket exists.

    Args:
        ticket_key: The Jira ticket key (e.g., 'PROJ-123').

    Returns:
        bool: True if ticket exists, False otherwise.
    """
    try:
        with JiraProvider() as provider:
            return bool(provider.validate_ticket_exists(ticket_key))
    except JiraProviderError as e:
        logger.warning(f"Could not validate Jira ticket: {e}")
        return False


def check_github_issue_exists(issue_number: str) -> bool:
    """Check if GitHub issue exists.

    Args:
        issue_number: The GitHub issue number.

    Returns:
        bool: True if issue exists, False otherwise.
    """
    try:
        origin = get_git_origin()
        owner, repo = extract_owner_repo(origin)
        with GitHubProvider() as provider:
            return bool(
                provider.validate_issue_exists(owner, repo, int(issue_number))
            )
    except (GitProviderError, GitHubProviderError, ValueError) as e:
        logger.warning(f"Could not validate GitHub issue: {e}")
        return False


def main() -> int:
    """Main entry point for validate_branch_name script.

    Returns:
        int: Exit code (0 for valid, 1 for invalid).
    """
    parser = argparse.ArgumentParser(
        description="Validate branch name against Jira/GitHub ticket patterns"
    )
    parser.add_argument("branch_name", help="The branch name to validate")
    parser.add_argument(
        "--check-exists",
        action="store_true",
        help="Verify the ticket/issue exists via API",
    )
    args = parser.parse_args()

    branch_name = args.branch_name
    logger.info("Validating branch name: %s", branch_name)

    # Check for Jira pattern
    jira_ticket = validate_jira_pattern(branch_name)
    if jira_ticket:
        logger.info("Found Jira ticket in branch name: %s", jira_ticket)
        if args.check_exists:
            if check_jira_ticket_exists(jira_ticket):
                print(f"✓ Valid branch name with Jira ticket: {jira_ticket}")
                return 0
            else:
                logger.error(f"Jira ticket {jira_ticket} does not exist")
                return 1
        else:
            print(f"✓ Valid branch name with Jira ticket: {jira_ticket}")
            return 0

    # Check for GitHub pattern
    github_issue = validate_github_pattern(branch_name)
    if github_issue:
        logger.info(f"Found GitHub issue in branch name: {github_issue}")
        if args.check_exists:
            if check_github_issue_exists(github_issue):
                print(f"✓ Valid branch name with GitHub issue: {github_issue}")
                return 0
            else:
                logger.error(f"GitHub issue {github_issue} does not exist")
                return 1
        else:
            print(f"✓ Valid branch name with GitHub issue: {github_issue}")
            return 0

    # No valid pattern found
    logger.error(
        f"Branch name '{branch_name}' does not match Jira (PROJ-123) "
        "or GitHub (gh123) patterns"
    )
    print(
        f"✗ Invalid branch name. Must contain either Jira ticket (PROJ-123) "
        "or GitHub issue (gh123)"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
