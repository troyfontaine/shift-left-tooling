#!/usr/bin/env python3
"""Query protected branches from a git repository provider.

This script extracts the origin from the current repository,
detects the provider (GitHub, GitLab, or Bitbucket),
and returns a list of protected branches.

Usage:
  python get_protected_branches.py [--json]

Options:
  --json    Output as JSON instead of plain text
  --help    Show this help message
"""

import argparse
import json
import logging
import sys
from typing import List

from lib.git_utils import (
    GitProvider,
    GitProviderError,
    detect_provider,
    extract_owner_repo,
    get_git_origin,
)
from lib.github_provider import GitHubProvider, GitHubProviderError
from lib.jira_provider import BitbucketProvider, GitLabProvider

logger = logging.getLogger(__name__)


def get_protected_branches_github(owner: str, repo: str) -> List[str]:
    """Get protected branches from GitHub.

    Args:
        owner: Repository owner.
        repo: Repository name.

    Returns:
        List[str]: List of protected branch names.

    Raises:
        GitHubProviderError: If unable to retrieve branches.
    """
    with GitHubProvider() as provider:
        return provider.get_protected_branches(owner, repo)


def get_protected_branches_gitlab(owner: str, repo: str) -> List[str]:
    """Get protected branches from GitLab.

    Args:
        owner: Repository owner.
        repo: Repository name.

    Returns:
        List[str]: List of protected branch names.

    Raises:
        NotImplementedError: GitLab is not yet supported.
    """
    provider = GitLabProvider()
    return provider.get_protected_branches(owner, repo)


def get_protected_branches_bitbucket(owner: str, repo: str) -> List[str]:
    """Get protected branches from Bitbucket.

    Args:
        owner: Repository owner.
        repo: Repository name.

    Returns:
        List[str]: List of protected branch names.

    Raises:
        NotImplementedError: Bitbucket is not yet supported.
    """
    provider = BitbucketProvider()
    return provider.get_protected_branches(owner, repo)


def main() -> int:
    """Main entry point for get_protected_branches script.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Query protected branches from the current git repository"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of plain text",
    )
    parser.add_argument(
        "--provider",
        choices=["github", "gitlab", "bitbucket"],
        help="Override provider detection",
    )
    args = parser.parse_args()

    try:
        # Get repository information
        logger.info("Detecting repository provider...")
        origin = get_git_origin()
        owner, repo = extract_owner_repo(origin)
        provider = args.provider or detect_provider(origin)

        logger.info("Repository: %s/%s, Provider: %s", owner, repo, provider)

        # Get protected branches based on provider
        protected_branches: List[str] = []
        if provider == GitProvider.GITHUB:
            protected_branches = get_protected_branches_github(owner, repo)
        elif provider == GitProvider.GITLAB:
            protected_branches = get_protected_branches_gitlab(owner, repo)
        elif provider == GitProvider.BITBUCKET:
            protected_branches = get_protected_branches_bitbucket(owner, repo)
        else:
            logger.error(
                "Provider '%s' not recognized or not supported", provider
            )
            return 1

        # Output results
        if args.json:
            output = {
                "provider": provider,
                "owner": owner,
                "repo": repo,
                "protected_branches": protected_branches,
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Protected branches in {owner}/{repo}:")
            if protected_branches:
                for branch in protected_branches:
                    print(f"  - {branch}")
            else:
                print("  (none)")

        return 0

    except GitProviderError as e:
        logger.error("Git provider error: %s", e)
        return 1
    except (GitHubProviderError, NotImplementedError) as e:
        logger.error("Error: %s", e)
        return 1
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
