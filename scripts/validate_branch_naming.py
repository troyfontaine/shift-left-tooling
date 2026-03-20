#!/usr/bin/env python3
"""Validate branch name follows naming conventions.

This script checks if a branch name follows the configured naming pattern
and validates against Jira and GitHub issue patterns.

Supports:
  - Jira ticket format (PROJ-123)
  - GitHub issue format (gh123, GH-456)
  - Configurable regex patterns

Usage:
  python validate_branch_naming.py [BRANCH_NAME]

Arguments:
  BRANCH_NAME    The branch name to validate (defaults to current branch)

Options:
  --pattern PATTERN    Override the naming pattern
  --check-exists       Verify GitHub/Jira issues exist
  --help               Show this help message

Environment Variables:
  BRANCH_NAMING_PATTERN    Regex pattern for branch naming (default: ^[A-Z]+-\\d+)
  GITHUB_TOKEN             GitHub API token (for validating issues)
  JIRA_URL                 Jira URL (for validating tickets)
  JIRA_TOKEN              Jira API token (for validating tickets)
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path to allow imports from lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.config import get_config
from lib.git_utils import (
    GitProviderError,
    get_current_branch,
    get_git_origin,
    extract_owner_repo,
)
from lib.github_provider import GitHubProvider, GitHubProviderError
from lib.jira_provider import JiraProvider, JiraProviderError

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


def extract_jira_ticket(branch_name: str) -> Optional[str]:
    """Extract Jira ticket from branch name.

    Args:
        branch_name: The branch name to extract from.

    Returns:
        Optional[str]: The Jira ticket ID if found, None otherwise.
    """
    match = re.search(r"\b([A-Z][A-Z0-9]*-\d+)\b", branch_name)
    if match:
        return match.group(1)
    return None


def extract_github_issue(branch_name: str) -> Optional[str]:
    """Extract GitHub issue number from branch name.

    Supports patterns like 'gh123', 'GH456', 'gh-789', 'GH-123'.

    Args:
        branch_name: The branch name to extract from.

    Returns:
        Optional[str]: The issue number if found, None otherwise.
    """
    match = re.search(r"[Gg][Hh][-]?(\d+)", branch_name)
    if match:
        return match.group(1)
    return None


def validate_jira_ticket(ticket_key: str) -> bool:
    """Validate that a Jira ticket exists.

    Args:
        ticket_key: The Jira ticket key (e.g., 'PROJ-123').

    Returns:
        bool: True if ticket exists, False otherwise.
    """
    try:
        with JiraProvider() as provider:
            return bool(provider.validate_ticket_exists(ticket_key))
    except JiraProviderError as e:
        logger.warning("Could not validate Jira ticket: %s", e)
        return False


def validate_github_issue(issue_number: str) -> bool:
    """Validate that a GitHub issue exists.

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
        logger.warning("Could not validate GitHub issue: %s", e)
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
    parser.add_argument(
        "--check-exists",
        action="store_true",
        help="Verify GitHub/Jira issues exist via API",
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

    # Check for GitHub issue
    github_issue = extract_github_issue(branch_name)
    if github_issue:
        logger.info("Found GitHub issue in branch name: %s", github_issue)
        if args.check_exists:
            if validate_github_issue(github_issue):
                print(
                    f"✓ Branch name '{branch_name}' is valid (GitHub issue #{github_issue})"
                )
                return 0
            else:
                print(
                    f"✗ GitHub issue #{github_issue} does not exist in repository"
                )
                return 1
        else:
            print(
                f"✓ Branch name '{branch_name}' is valid (GitHub issue #{github_issue})"
            )
            return 0

    # Check for Jira ticket
    jira_ticket = extract_jira_ticket(branch_name)
    if jira_ticket:
        logger.info("Found Jira ticket in branch name: %s", jira_ticket)
        if args.check_exists:
            if validate_jira_ticket(jira_ticket):
                print(
                    f"✓ Branch name '{branch_name}' is valid (Jira ticket {jira_ticket})"
                )
                return 0
            else:
                print(f"✗ Jira ticket {jira_ticket} does not exist")
                return 1
        else:
            print(
                f"✓ Branch name '{branch_name}' is valid (Jira ticket {jira_ticket})"
            )
            return 0

    # Fall back to regex pattern validation
    logger.info("Checking against pattern: %s", pattern)
    if validate_branch_naming(branch_name, pattern):
        print(f"✓ Branch name '{branch_name}' is valid")
        return 0
    else:
        print(
            f"✗ Branch name '{branch_name}' does not match the required pattern:\n"
            f"  Pattern: {pattern}\n"
            f"  Supported formats:\n"
            f"    - Jira: PROJ-123 (e.g., PROJ-123-feature-description)\n"
            f"    - GitHub: gh123 or GH-456 (e.g., gh42-feature-description)\n"
            f"    - Custom: {pattern} (e.g., PROJ-123-feature-description)"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
