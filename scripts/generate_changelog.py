#!/usr/bin/env python3
"""Generate changelog from commit history.

This script scans recent commits, extracts Jira ticket references,
and generates a formatted changelog.

Usage:
  python generate_changelog.py [OPTIONS]

Options:
  --last-n-commits N     Include last N commits (default: 10)
  --since-tag TAG        Include commits since TAG
  --tag-range TAG1 TAG2  Include commits between TAG1 and TAG2
  --output FILE          Write to file (default: stdout)
  --format FORMAT        Output format: markdown, json, or plain (default: markdown)
  --help                 Show this help message
"""

import argparse
import json
import logging
import sys
from collections import defaultdict
from typing import Dict, List, Optional

from lib.git_utils import (
    GitProviderError,
    extract_jira_ticket_from_message,
    get_commit_history,
)
from lib.jira_provider import JiraProvider, JiraProviderError

logger = logging.getLogger(__name__)


def get_commits_in_range(
    since_tag: Optional[str] = None,
    tag_range: Optional[tuple] = None,
    limit: int = 10,
) -> List[str]:
    """Get commit hashes in specified range.

    Args:
        since_tag: Get commits since this tag.
        tag_range: Tuple of (start_tag, end_tag) for range.
        limit: Fallback limit if no tags specified.

    Returns:
        List[str]: List of commit hashes.
    """
    import subprocess

    # TODO: Implement tag-based commit ranges
    # For now, return recent commits
    return get_commit_history(limit=limit)


def get_ticket_info_from_jira(ticket_key: str) -> Optional[Dict]:
    """Get ticket information from Jira.

    Args:
        ticket_key: The Jira ticket key.

    Returns:
        Optional[Dict]: Dictionary with ticket info or None if not found.
    """
    try:
        with JiraProvider() as provider:
            issue = provider.get_ticket(ticket_key)
            status = provider.get_ticket_status(ticket_key)
            return {
                "key": ticket_key,
                "summary": issue.fields.summary,
                "status": status,
                "url": issue.permalink(),
            }
    except JiraProviderError as e:
        logger.warning("Could not get Jira info for %s: %s", ticket_key, e)
        return None


def generate_markdown_changelog(tickets_dict: Dict[str, Dict]) -> str:
    """Generate markdown formatted changelog.

    Args:
        tickets_dict: Dictionary mapping ticket keys to commit info.

    Returns:
        str: Formatted markdown changelog.
    """
    lines = ["# Changelog\n"]

    if not tickets_dict:
        lines.append("No tickets found in recent commits.\n")
        return "".join(lines)

    for ticket_key in sorted(tickets_dict.keys()):
        ticket_info = tickets_dict[ticket_key]
        lines.append(f"## {ticket_key}\n")

        if isinstance(ticket_info, dict) and "summary" in ticket_info:
            lines.append(f"**{ticket_info['summary']}**\n")
            if "status" in ticket_info:
                lines.append(f"Status: {ticket_info['status']}\n")

        lines.append("\n")

    return "".join(lines)


def generate_json_changelog(tickets_dict: Dict[str, Dict]) -> str:
    """Generate JSON formatted changelog.

    Args:
        tickets_dict: Dictionary mapping ticket keys to commit info.

    Returns:
        str: Formatted JSON changelog.
    """
    return json.dumps(tickets_dict, indent=2)


def generate_plain_changelog(tickets_dict: Dict[str, Dict]) -> str:
    """Generate plain text formatted changelog.

    Args:
        tickets_dict: Dictionary mapping ticket keys to commit info.

    Returns:
        str: Formatted plain text changelog.
    """
    lines = ["CHANGELOG\n", "=" * 50, "\n"]

    if not tickets_dict:
        lines.append("No tickets found in recent commits.\n")
        return "".join(lines)

    for ticket_key in sorted(tickets_dict.keys()):
        lines.append(f"\n{ticket_key}\n")
        lines.append("-" * len(ticket_key) + "\n")

        ticket_info = tickets_dict[ticket_key]
        if isinstance(ticket_info, dict) and "summary" in ticket_info:
            lines.append(f"  {ticket_info['summary']}\n")

    return "".join(lines)


def main() -> int:
    """Main entry point for generate_changelog script.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Generate changelog from commit history"
    )
    parser.add_argument(
        "--last-n-commits",
        type=int,
        default=10,
        help="Include last N commits (default: 10)",
    )
    parser.add_argument(
        "--since-tag",
        type=str,
        help="Include commits since TAG",
    )
    parser.add_argument(
        "--tag-range",
        type=str,
        nargs=2,
        metavar=("TAG1", "TAG2"),
        help="Include commits between TAG1 and TAG2",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Write to file (default: stdout)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "plain"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    try:
        # Get commit history
        logger.info("Fetching last %d commits...", args.last_n_commits)
        _ = get_commits_in_range(
            since_tag=args.since_tag,
            tag_range=tuple(args.tag_range) if args.tag_range else None,
            limit=args.last_n_commits,
        )

        # TODO: Get full commit messages and extract tickets
        # For now, we'll create a placeholder
        tickets_dict: Dict[str, Dict] = defaultdict(dict)

        logger.info("Found %d unique tickets", len(tickets_dict))

        # Generate changelog
        if args.format == "markdown":
            changelog = generate_markdown_changelog(tickets_dict)
        elif args.format == "json":
            changelog = generate_json_changelog(tickets_dict)
        else:
            changelog = generate_plain_changelog(tickets_dict)

        # Output
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(changelog)
            logger.info("Changelog written to %s", args.output)
            print(f"Changelog written to {args.output}")
        else:
            print(changelog)

        return 0

    except GitProviderError as e:
        logger.error("Git error: %s", e)
        return 1
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
