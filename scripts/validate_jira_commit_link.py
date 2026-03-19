#!/usr/bin/env python3
"""Validate that commits reference valid Jira tickets.

This script checks commit messages for Jira ticket references (e.g., PROJ-123)
and optionally verifies the ticket exists in Jira.

This is typically used as a commit-msg hook.

Usage:
  python validate_jira_commit_link.py [--check-exists]

Options:
  --check-exists    Verify ticket exists in Jira
  --help            Show this help message

Environment Variables:
  JIRA_URL          Jira instance URL
  JIRA_TOKEN        Jira API token
"""

import argparse
import logging
import sys

from lib.git_utils import (
    GitProviderError,
    extract_jira_ticket_from_message,
    get_commit_message,
)
from lib.jira_provider import JiraProvider, JiraProviderError

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for validate_jira_commit_link script.

    Returns:
        int: Exit code (0 for valid, 1 for invalid).
    """
    parser = argparse.ArgumentParser(
        description="Validate that commits reference Jira tickets"
    )
    parser.add_argument(
        "--check-exists",
        action="store_true",
        help="Verify the ticket exists in Jira",
    )
    args = parser.parse_args()

    try:
        # Get commit message
        commit_message = get_commit_message()
        logger.info("Commit message retrieved")

        # Extract Jira ticket from message
        ticket_key = extract_jira_ticket_from_message(commit_message)

        if not ticket_key:
            print(
                "✗ Commit message does not reference a Jira ticket.\n"
                "Commit messages should include a ticket reference like: PROJ-123\n"
                "Example: 'PROJ-123: Implement new feature'"
            )
            return 1

        logger.info("Found Jira ticket reference: %s", ticket_key)

        # Optionally check if ticket exists
        if args.check_exists:
            try:
                with JiraProvider() as provider:
                    if provider.validate_ticket_exists(ticket_key):
                        print(
                            f"✓ Commit references valid Jira ticket: {ticket_key}"
                        )
                        return 0
                    print(f"✗ Jira ticket {ticket_key} does not exist")
                    return 1
            except JiraProviderError as e:
                logger.warning("Could not verify Jira ticket: %s", e)
                logger.warning("Allowing commit (Jira verification failed)")
                print(
                    f"✓ Commit references Jira ticket: {ticket_key} (verification skipped)"
                )
                return 0
        else:
            print(f"✓ Commit references Jira ticket: {ticket_key}")
            return 0

    except GitProviderError as e:
        logger.error("Git error: %s", e)
        print(f"✗ Error retrieving commit message: {e}")
        return 1
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
