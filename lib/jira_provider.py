"""Jira provider for shift-left-tooling.

Provides functions for Jira API operations including:
- Getting Jira tickets
- Validating Jira ticket existence
- Stub implementations for BitBucket and GitLab
"""

import logging
from typing import Optional

from jira import JIRA, JIRAError

from .config import get_config

logger = logging.getLogger(__name__)


class JiraProviderError(Exception):
    """Raised when Jira provider operations fail."""


class JiraProvider:
    """Provider for Jira API operations."""

    def __init__(self, url: Optional[str] = None, token: Optional[str] = None):
        """Initialize the Jira provider.

        Args:
            url: Jira instance URL. If not provided, uses JIRA_URL env var.
            token: Jira API token. If not provided, uses JIRA_TOKEN env var.

        Raises:
            JiraProviderError: If no URL or token is available.
        """
        config = get_config()
        self.url = url or config.jira.url
        self.token = token or config.jira.token

        if not self.url:
            raise JiraProviderError(
                "Jira URL is required. Set JIRA_URL environment variable."
            )

        if not self.token:
            logger.warning("Jira token not provided. Some operations may fail.")
            self.client = None
        else:
            try:
                # Use API token authentication
                self.client = JIRA(
                    server=self.url,
                    basic_auth=("automation", self.token),
                )
                # Validate connection by getting server info
                self.client.server_info()
                logger.debug("Jira provider initialized successfully")
            except JIRAError as e:
                raise JiraProviderError(
                    f"Failed to authenticate with Jira: {e}"
                ) from e

    def get_ticket(self, ticket_key: str):
        """Get a Jira ticket by key.

        Args:
            ticket_key: The Jira ticket key (e.g., 'PROJ-123').

        Returns:
            Issue: The Jira issue object.

        Raises:
            JiraProviderError: If ticket is not found or API call fails.
        """
        if not self.client:
            raise JiraProviderError(
                "Jira client not initialized. Token may be missing."
            )

        try:
            issue = self.client.issue(ticket_key)
            logger.debug("Found Jira ticket %s", ticket_key)
            return issue
        except JIRAError as e:
            raise JiraProviderError(
                f"Failed to get Jira ticket {ticket_key}: {e}"
            ) from e

    def validate_ticket_exists(self, ticket_key: str) -> bool:
        """Validate that a Jira ticket exists.

        Args:
            ticket_key: The Jira ticket key (e.g., 'PROJ-123').

        Returns:
            bool: True if ticket exists, False otherwise.
        """
        if not self.client:
            logger.warning(
                "Jira client not initialized. Cannot validate ticket."
            )
            return False

        try:
            self.get_ticket(ticket_key)
            logger.debug("Jira ticket %s exists", ticket_key)
            return True
        except JiraProviderError:
            logger.debug("Jira ticket %s not found", ticket_key)
            return False

    def get_ticket_status(self, ticket_key: str) -> Optional[str]:
        """Get the status of a Jira ticket.

        Args:
            ticket_key: The Jira ticket key.

        Returns:
            Optional[str]: The ticket status or None if not found.
        """
        try:
            issue = self.get_ticket(ticket_key)
            return issue.fields.status.name
        except JiraProviderError:
            return None

    def close(self) -> None:
        """Close the Jira client connection."""
        if self.client:
            self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class BitbucketProvider:
    """Stub provider for Bitbucket - not yet implemented."""

    def __init__(self):
        """Initialize Bitbucket provider."""
        logger.warning("Bitbucket provider is not yet implemented")

    def get_protected_branches(self, owner: str, repo: str):
        """Get protected branches - not implemented."""
        raise NotImplementedError(
            "Bitbucket support is not yet implemented. Please use GitHub or Jira for now."
        )

    def validate_issue_exists(self, issue_key: str):
        """Validate issue - not implemented."""
        raise NotImplementedError(
            "Bitbucket support is not yet implemented. Please use GitHub or Jira for now."
        )


class GitLabProvider:
    """Stub provider for GitLab - not yet implemented."""

    def __init__(self):
        """Initialize GitLab provider."""
        logger.warning("GitLab provider is not yet implemented")

    def get_protected_branches(self, owner: str, repo: str):
        """Get protected branches - not implemented."""
        raise NotImplementedError(
            "GitLab support is not yet implemented. Please use GitHub or Jira for now."
        )

    def validate_issue_exists(self, issue_key: str):
        """Validate issue - not implemented."""
        raise NotImplementedError(
            "GitLab support is not yet implemented. Please use GitHub or Jira for now."
        )
