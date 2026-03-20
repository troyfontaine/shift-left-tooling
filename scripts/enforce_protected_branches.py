#!/usr/bin/env python3
"""Prevent pushes to protected branches.

This script is meant to be used as a pre-push hook.
It checks the current branch against the list of protected branches
and prevents the push if the current branch is protected.

Usage:
  python enforce_protected_branches.py

Environment Variables:
  GITHUB_TOKEN    Required for GitHub API access
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path to allow imports from lib
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.git_utils import (
    GitProvider,
    GitProviderError,
    detect_provider,
    get_current_branch,
    get_git_origin,
    extract_owner_repo,
)
from lib.github_provider import (
    GitHubProvider,
    GitHubProviderError,
)

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for enforce_protected_branches script.

    Returns:
        int: Exit code (0 for allow push, 1 for block push).
    """
    try:
        # Get current branch
        current_branch = get_current_branch()
        logger.info("Current branch: %s", current_branch)

        # Get repository information
        origin = get_git_origin()
        owner, repo = extract_owner_repo(origin)
        provider = detect_provider(origin)

        logger.info("Repository: %s/%s, Provider: %s", owner, repo, provider)

        # Check protected branches based on provider
        if provider == GitProvider.GITHUB:
            with GitHubProvider() as github_provider:
                protected_branches = github_provider.get_protected_branches(
                    owner, repo
                )
        else:
            logger.warning(
                "Provider '%s' is not yet supported for branch enforcement",
                provider,
            )
            logger.info(
                "Allowing push (protection not available for this provider)"
            )
            return 0

        # Check if current branch is protected
        if current_branch in protected_branches:
            print(
                f"✗ ERROR: Cannot push to protected branch '{current_branch}'\n"
                f"Protected branches in {owner}/{repo}:"
            )
            for branch in protected_branches:
                print(f"  - {branch}")
            print(
                "\nTo push to this branch, contact a repository administrator."
            )
            return 1

        logger.info(
            "Branch '%s' is not protected. Push allowed.", current_branch
        )
        return 0

    except GitProviderError as e:
        logger.error("Git provider error: %s", e)
        logger.error("Blocking push due to git provider error")
        return 1
    except GitHubProviderError as e:
        logger.error("GitHub error: %s", e)
        logger.error("Blocking push due to GitHub error")
        return 1
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error: %s", e)
        logger.error("Blocking push due to unexpected error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
