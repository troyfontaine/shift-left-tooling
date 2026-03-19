"""GitHub provider for shift-left-tooling.

Provides functions for GitHub API operations including:
- Querying protected branches
- Validating GitHub issues
- Getting repository information
"""

import logging
from typing import List, Optional

from github import Github, GithubException, Repository

from .config import get_config

logger = logging.getLogger(__name__)


class GitHubProviderError(Exception):
    """Raised when GitHub provider operations fail."""


class GitHubProvider:
    """Provider for GitHub API operations."""

    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub provider.

        Args:
            token: GitHub personal access token. If not provided, uses GITHUB_TOKEN env var.

        Raises:
            GitHubProviderError: If no token is available.
        """
        config = get_config()
        self.token = token or config.github.token

        if not self.token:
            raise GitHubProviderError(
                "GitHub token is required. Set GITHUB_TOKEN environment variable."
            )

        try:
            self.client = Github(self.token, base_url="https://api.github.com")
            # Validate token by attempting to get authenticated user
            _ = self.client.get_user().login
            logger.debug("GitHub provider initialized successfully")
        except GithubException as e:
            raise GitHubProviderError(
                f"Failed to authenticate with GitHub: {e}"
            ) from e

    def get_repository(self, owner: str, repo: str) -> Repository.Repository:
        """Get a GitHub repository object.

        Args:
            owner: The repository owner (username or organization).
            repo: The repository name.

        Returns:
            Repository: The GitHub repository object.

        Raises:
            GitHubProviderError: If repository is not found or API call fails.
        """
        try:
            return self.client.get_user(owner).get_repo(repo)
        except GithubException as e:
            raise GitHubProviderError(
                f"Failed to get repository {owner}/{repo}: {e}"
            ) from e

    def get_protected_branches(self, owner: str, repo: str) -> List[str]:
        """Get list of protected branches in a repository.

        Args:
            owner: The repository owner (username or organization).
            repo: The repository name.

        Returns:
            List[str]: List of protected branch names.

        Raises:
            GitHubProviderError: If API call fails.
        """
        try:
            repository = self.get_repository(owner, repo)
            protected_branches = []

            # Iterate through all branches and check protection status
            for branch in repository.get_branches():
                try:
                    # Check if branch has protection rules
                    branch.get_protection()
                    protected_branches.append(branch.name)
                except GithubException as e:
                    # If 404, branch is not protected
                    if e.status == 404:
                        continue
                    # Re-raise other exceptions
                    raise

            logger.info(
                "Found %d protected branches in %s/%s",
                len(protected_branches),
                owner,
                repo,
            )
            return protected_branches
        except GitHubProviderError:
            raise
        except GithubException as e:
            raise GitHubProviderError(
                f"Failed to get protected branches for {owner}/{repo}: {e}"
            ) from e

    def get_issue(self, owner: str, repo: str, issue_number: int):
        """Get a GitHub issue by number.

        Args:
            owner: The repository owner (username or organization).
            repo: The repository name.
            issue_number: The issue number.

        Returns:
            Issue: The GitHub issue object.

        Raises:
            GitHubProviderError: If issue is not found or API call fails.
        """
        try:
            repository = self.get_repository(owner, repo)
            return repository.get_issue(issue_number)
        except GithubException as e:
            raise GitHubProviderError(
                f"Failed to get issue #{issue_number} in {owner}/{repo}: {e}"
            ) from e

    def validate_issue_exists(
        self, owner: str, repo: str, issue_number: int
    ) -> bool:
        """Validate that a GitHub issue exists.

        Args:
            owner: The repository owner (username or organization).
            repo: The repository name.
            issue_number: The issue number to validate.

        Returns:
            bool: True if issue exists, False otherwise.
        """
        try:
            self.get_issue(owner, repo, issue_number)
            logger.debug("Issue #%d exists in %s/%s", issue_number, owner, repo)
            return True
        except GitHubProviderError:
            logger.debug(
                "Issue #%d not found in %s/%s", issue_number, owner, repo
            )
            return False

    def validate_branch_is_protected(
        self, owner: str, repo: str, branch_name: str
    ) -> bool:
        """Check if a specific branch is protected.

        Args:
            owner: The repository owner (username or organization).
            repo: The repository name.
            branch_name: The branch name to check.

        Returns:
            bool: True if branch is protected, False otherwise.

        Raises:
            GitHubProviderError: If API call fails.
        """
        try:
            repository = self.get_repository(owner, repo)
            branch = repository.get_branch(branch_name)
            branch.get_protection()
            return True
        except GithubException as e:
            if e.status == 404:
                # Branch either doesn't exist or isn't protected
                logger.debug(
                    "Branch %s is not protected or doesn't exist", branch_name
                )
                return False
            raise GitHubProviderError(
                f"Failed to check protection status of {branch_name} in {owner}/{repo}: {e}"
            ) from e

    def close(self) -> None:
        """Close the GitHub client connection."""
        # PyGithub doesn't require explicit cleanup, but we keep this for API consistency

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
