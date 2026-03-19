"""Git utilities for shift-left-tooling.

Provides functions for git repository operations including:
- Detecting git repository and extracting origin URL
- Identifying the git provider (GitHub, GitLab, Bitbucket)
- Getting current branch name
- Parsing commit messages
"""

import logging
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class GitProviderError(Exception):
    """Raised when git provider operations fail."""


class GitProvider:
    """Enumeration of supported git providers."""

    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    UNKNOWN = "unknown"

    def __init__(self):
        """GitProvider is not meant to be instantiated."""


def get_git_root() -> Path:
    """Get the root directory of the current git repository.

    Returns:
        Path: The root directory of the git repository.

    Raises:
        GitProviderError: If not in a git repository.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise GitProviderError("Not in a git repository") from e


def get_git_origin() -> str:
    """Get the origin remote URL for the current git repository.

    Returns:
        str: The origin remote URL.

    Raises:
        GitProviderError: If origin remote is not configured.
    """
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True,
        )
        origin = result.stdout.strip()
        if not origin:
            raise GitProviderError("No origin remote configured")
        return origin
    except subprocess.CalledProcessError as e:
        raise GitProviderError("Failed to get git origin") from e


def detect_provider(origin_url: str) -> str:
    """Detect the git provider from an origin URL.

    Args:
        origin_url: The origin URL from git config.

    Returns:
        str: The detected provider (github, gitlab, bitbucket, or unknown).
    """
    origin_lower = origin_url.lower()

    if "github.com" in origin_lower:
        return GitProvider.GITHUB
    if "gitlab.com" in origin_lower or "gitlab" in origin_lower:
        return GitProvider.GITLAB
    if "bitbucket.org" in origin_lower or "bitbucket" in origin_lower:
        return GitProvider.BITBUCKET
    return GitProvider.UNKNOWN


def extract_owner_repo(origin_url: str) -> Tuple[str, str]:
    """Extract owner and repository name from a git origin URL.

    Args:
        origin_url: The origin URL from git config.

    Returns:
        Tuple[str, str]: A tuple of (owner, repo).

    Raises:
        GitProviderError: If the URL format is invalid.
    """
    # Handle both SSH and HTTPS URLs
    # SSH: git@github.com:owner/repo.git
    # HTTPS: https://github.com/owner/repo.git

    # Remove .git suffix if present
    url = origin_url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]

    # Try SSH format first
    ssh_match = re.match(r"git@[^:]+:(.+)/(.+)$", url)
    if ssh_match:
        return ssh_match.group(1), ssh_match.group(2)

    # Try HTTPS format
    https_match = re.match(r"https?://[^/]+/(.+)/(.+)$", url)
    if https_match:
        return https_match.group(1), https_match.group(2)

    raise GitProviderError(f"Could not parse owner/repo from: {origin_url}")


def get_current_branch() -> str:
    """Get the current git branch name.

    Returns:
        str: The current branch name.

    Raises:
        GitProviderError: If unable to determine current branch.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitProviderError("Failed to get current branch") from e


def get_commit_message() -> str:
    """Get the message of the current commit or staged changes.

    Returns:
        str: The commit message.

    Raises:
        GitProviderError: If unable to retrieve commit message.
    """
    try:
        # First try to get the HEAD commit message
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            capture_output=True,
            text=True,
            check=True,
        )
        message = result.stdout.strip()
        if message:
            return message

        # If HEAD is empty, try to get from index
        result = subprocess.run(
            ["git", "diff", "--cached", "--", "*.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitProviderError("Failed to get commit message") from e


def get_commit_history(limit: int = 10) -> list[str]:
    """Get recent commit hashes.

    Args:
        limit: Number of recent commits to retrieve.

    Returns:
        list[str]: List of commit hashes.

    Raises:
        GitProviderError: If unable to retrieve commit history.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-n{limit}"],
            capture_output=True,
            text=True,
            check=True,
        )
        commits = [
            line.split()[0]
            for line in result.stdout.strip().split("\n")
            if line
        ]
        return commits
    except subprocess.CalledProcessError as e:
        raise GitProviderError("Failed to get commit history") from e


def extract_jira_ticket_from_message(message: str) -> Optional[str]:
    """Extract Jira ticket ID from a commit message.

    Args:
        message: The commit message text.

    Returns:
        Optional[str]: The Jira ticket ID (e.g., 'PROJ-123') or None if not found.
    """
    # Match common Jira ticket patterns like PROJ-123, MYAPP-456
    match = re.search(r"\b([A-Z][A-Z0-9]*-\d+)\b", message)
    if match:
        return match.group(1)
    return None


def extract_github_issue_from_message(message: str) -> Optional[str]:
    """Extract GitHub issue reference from a commit message.

    Supports patterns like '#123', 'gh123', 'GH456', 'gh-789', 'GH-123'.
    When 'gh-' variant (with dash) is detected, logs a note that Jira will not be checked.

    Args:
        message: The commit message text.

    Returns:
        Optional[str]: The GitHub issue ID (e.g., '123') or None if not found.
    """
    # Match GitHub issue patterns: #123, gh123, GH456, gh-789, GH-123
    match = re.search(r"#(\d+)|[Gg][Hh][-]?(\d+)", message)
    if match:
        # Extract the issue number from either group
        issue_number = match.group(1) or match.group(2)
        # Check if the variant with dash was used (e.g., 'gh-123')
        if re.search(r"[Gg][Hh]-(\d+)", message):
            logger.info(
                "Detected 'gh-' variant in commit message; Jira checking skipped"
            )
        return issue_number
    return None
