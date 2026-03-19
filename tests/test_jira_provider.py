"""Tests for Jira provider module."""

from unittest import mock
import pytest
from jira import JIRAError

from lib.jira_provider import JiraProvider, JiraProviderError, BitbucketProvider, GitLabProvider


class TestJiraProvider:
    """Tests for JiraProvider class."""

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_init_with_token(self, mock_jira_client, mock_get_config):
        """Test initializing JiraProvider with token."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = "test-token"
        mock_get_config.return_value = mock_config

        mock_client = mock.MagicMock()
        mock_client.server_info.return_value = {}
        mock_jira_client.return_value = mock_client

        provider = JiraProvider()
        assert provider.url == "https://jira.example.com"
        assert provider.token == "test-token"
        assert provider.client is not None

    @mock.patch("lib.jira_provider.get_config")
    def test_init_without_url(self, mock_get_config):
        """Test JiraProvider raises error without URL."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = None
        mock_config.jira.token = "test-token"
        mock_get_config.return_value = mock_config

        with pytest.raises(JiraProviderError):
            JiraProvider()

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_init_without_token(self, mock_jira_client, mock_get_config):
        """Test JiraProvider initializes without token but logs warning."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = None
        mock_get_config.return_value = mock_config

        provider = JiraProvider()
        assert provider.url == "https://jira.example.com"
        assert provider.token is None
        assert provider.client is None

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_init_auth_error(self, mock_jira_client, mock_get_config):
        """Test JiraProvider raises error on auth failure."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = "bad-token"
        mock_get_config.return_value = mock_config

        mock_jira_client.side_effect = JIRAError("Invalid token")

        with pytest.raises(JiraProviderError):
            JiraProvider()

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_get_ticket_success(self, mock_jira_client, mock_get_config):
        """Test getting a Jira ticket successfully."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = "test-token"
        mock_get_config.return_value = mock_config

        mock_client = mock.MagicMock()
        mock_client.server_info.return_value = {}
        mock_issue = mock.MagicMock()
        mock_client.issue.return_value = mock_issue
        mock_jira_client.return_value = mock_client

        provider = JiraProvider()
        result = provider.get_ticket("PROJ-123")
        assert result == mock_issue

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_get_ticket_without_client(self, mock_jira_client, mock_get_config):
        """Test getting ticket when client is not initialized."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = None
        mock_get_config.return_value = mock_config

        provider = JiraProvider()
        with pytest.raises(JiraProviderError):
            provider.get_ticket("PROJ-123")

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_get_ticket_not_found(self, mock_jira_client, mock_get_config):
        """Test getting ticket that doesn't exist."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = "test-token"
        mock_get_config.return_value = mock_config

        mock_client = mock.MagicMock()
        mock_client.server_info.return_value = {}
        mock_client.issue.side_effect = JIRAError("Not found")
        mock_jira_client.return_value = mock_client

        provider = JiraProvider()
        with pytest.raises(JiraProviderError):
            provider.get_ticket("PROJ-999")

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_validate_ticket_exists_true(self, mock_jira_client, mock_get_config):
        """Test validating ticket exists returns True."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = "test-token"
        mock_get_config.return_value = mock_config

        mock_client = mock.MagicMock()
        mock_client.server_info.return_value = {}
        mock_issue = mock.MagicMock()
        mock_client.issue.return_value = mock_issue
        mock_jira_client.return_value = mock_client

        provider = JiraProvider()
        result = provider.validate_ticket_exists("PROJ-123")
        assert result is True

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_validate_ticket_exists_false(self, mock_jira_client, mock_get_config):
        """Test validating ticket exists returns False."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = "test-token"
        mock_get_config.return_value = mock_config

        mock_client = mock.MagicMock()
        mock_client.server_info.return_value = {}
        mock_client.issue.side_effect = JIRAError("Not found")
        mock_jira_client.return_value = mock_client

        provider = JiraProvider()
        result = provider.validate_ticket_exists("PROJ-999")
        assert result is False

    @mock.patch("lib.jira_provider.get_config")
    def test_validate_ticket_exists_no_client(self, mock_get_config):
        """Test validating ticket when client is not initialized."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = None
        mock_get_config.return_value = mock_config

        provider = JiraProvider()
        result = provider.validate_ticket_exists("PROJ-123")
        assert result is False

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_get_ticket_status_success(self, mock_jira_client, mock_get_config):
        """Test getting ticket status successfully."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = "test-token"
        mock_get_config.return_value = mock_config

        mock_client = mock.MagicMock()
        mock_client.server_info.return_value = {}
        mock_issue = mock.MagicMock()
        mock_issue.fields.status.name = "IN PROGRESS"
        mock_client.issue.return_value = mock_issue
        mock_jira_client.return_value = mock_client

        provider = JiraProvider()
        result = provider.get_ticket_status("PROJ-123")
        assert result == "IN PROGRESS"

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_get_ticket_status_not_found(self, mock_jira_client, mock_get_config):
        """Test getting status when ticket not found."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = "test-token"
        mock_get_config.return_value = mock_config

        mock_client = mock.MagicMock()
        mock_client.server_info.return_value = {}
        mock_client.issue.side_effect = JIRAError("Not found")
        mock_jira_client.return_value = mock_client

        provider = JiraProvider()
        result = provider.get_ticket_status("PROJ-999")
        assert result is None

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_close(self, mock_jira_client, mock_get_config):
        """Test closing provider."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = "test-token"
        mock_get_config.return_value = mock_config

        mock_client = mock.MagicMock()
        mock_client.server_info.return_value = {}
        mock_jira_client.return_value = mock_client

        provider = JiraProvider()
        provider.close()
        mock_client.close.assert_called_once()

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_close_without_client(self, mock_jira_client, mock_get_config):
        """Test closing when client is not initialized."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = None
        mock_get_config.return_value = mock_config

        provider = JiraProvider()
        provider.close()  # Should not raise

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_context_manager(self, mock_jira_client, mock_get_config):
        """Test context manager functionality."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://jira.example.com"
        mock_config.jira.token = "test-token"
        mock_get_config.return_value = mock_config

        mock_client = mock.MagicMock()
        mock_client.server_info.return_value = {}
        mock_jira_client.return_value = mock_client

        with JiraProvider() as provider:
            assert provider.client is not None

        mock_client.close.assert_called_once()

    @mock.patch("lib.jira_provider.get_config")
    @mock.patch("lib.jira_provider.JIRA")
    def test_init_with_explicit_credentials(self, mock_jira_client, mock_get_config):
        """Test initializing with explicit credentials."""
        mock_config = mock.MagicMock()
        mock_config.jira.url = "https://default.jira.com"
        mock_config.jira.token = "default-token"
        mock_get_config.return_value = mock_config

        mock_client = mock.MagicMock()
        mock_client.server_info.return_value = {}
        mock_jira_client.return_value = mock_client

        provider = JiraProvider(
            url="https://custom.jira.com",
            token="custom-token"
        )
        assert provider.url == "https://custom.jira.com"
        assert provider.token == "custom-token"


class TestBitbucketProvider:
    """Tests for BitbucketProvider stub."""

    def test_init(self):
        """Test BitbucketProvider initialization."""
        provider = BitbucketProvider()
        assert provider is not None

    def test_get_protected_branches_not_implemented(self):
        """Test that get_protected_branches raises NotImplementedError."""
        provider = BitbucketProvider()
        with pytest.raises(NotImplementedError):
            provider.get_protected_branches("owner", "repo")

    def test_validate_issue_exists_not_implemented(self):
        """Test that validate_issue_exists raises NotImplementedError."""
        provider = BitbucketProvider()
        with pytest.raises(NotImplementedError):
            provider.validate_issue_exists("BB-123")


class TestGitLabProvider:
    """Tests for GitLabProvider stub."""

    def test_init(self):
        """Test GitLabProvider initialization."""
        provider = GitLabProvider()
        assert provider is not None

    def test_get_protected_branches_not_implemented(self):
        """Test that get_protected_branches raises NotImplementedError."""
        provider = GitLabProvider()
        with pytest.raises(NotImplementedError):
            provider.get_protected_branches("owner", "repo")

    def test_validate_issue_exists_not_implemented(self):
        """Test that validate_issue_exists raises NotImplementedError."""
        provider = GitLabProvider()
        with pytest.raises(NotImplementedError):
            provider.validate_issue_exists("GL-123")
