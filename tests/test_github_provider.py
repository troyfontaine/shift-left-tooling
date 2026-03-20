"""Tests for github_provider module."""

from unittest import mock

import pytest
from github import GithubException

from lib.github_provider import GitHubProvider, GitHubProviderError


class TestGitHubProvider:
    """Tests for GitHubProvider."""

    @mock.patch("lib.github_provider.Github")
    def test_init_with_valid_token(self, mock_github_class):
        """Test initialization with valid token."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        provider = GitHubProvider(token="ghp_test123")
        assert provider.token == "ghp_test123"
        assert provider.client == mock_client

    @mock.patch("lib.github_provider.get_config")
    def test_init_without_token_from_env(self, mock_get_config):
        """Test initialization without token uses env var."""
        mock_config = mock.MagicMock()
        mock_config.github.token = None
        mock_get_config.return_value = mock_config

        with pytest.raises(GitHubProviderError):
            GitHubProvider()

    @mock.patch("lib.github_provider.Github")
    def test_init_auth_failure(self, mock_github_class):
        """Test initialization fails with invalid token."""
        mock_github_class.side_effect = GithubException(
            401, {"message": "Bad credentials"}
        )

        with pytest.raises(GitHubProviderError):
            GitHubProvider(token="ghp_invalid")

    @mock.patch("lib.github_provider.Github")
    def test_get_repository_success(self, mock_github_class):
        """Test getting a repository."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        mock_repo = mock.MagicMock()
        mock_user.get_repo.return_value = mock_repo

        provider = GitHubProvider(token="ghp_test123")
        result = provider.get_repository("owner", "repo")
        assert result == mock_repo

    @mock.patch("lib.github_provider.Github")
    def test_get_repository_not_found(self, mock_github_class):
        """Test getting a repository that doesn't exist."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user
        mock_user.get_repo.side_effect = GithubException(
            404, {"message": "Not Found"}
        )

        provider = GitHubProvider(token="ghp_test123")
        with pytest.raises(GitHubProviderError):
            provider.get_repository("owner", "nonexistent")

    @mock.patch("lib.github_provider.Github")
    def test_get_protected_branches_success(self, mock_github_class):
        """Test getting protected branches."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        mock_branch1 = mock.MagicMock()
        mock_branch1.name = "main"
        mock_branch2 = mock.MagicMock()
        mock_branch2.name = "develop"

        mock_repo = mock.MagicMock()
        mock_repo.get_branches.return_value = [mock_branch1, mock_branch2]
        mock_branch1.get_protection.return_value = mock.MagicMock()
        mock_branch2.get_protection.return_value = mock.MagicMock()

        mock_user.get_repo.return_value = mock_repo

        provider = GitHubProvider(token="ghp_test123")
        result = provider.get_protected_branches("owner", "repo")
        assert "main" in result
        assert "develop" in result

    @mock.patch("lib.github_provider.Github")
    def test_get_protected_branches_with_unprotected(self, mock_github_class):
        """Test getting protected branches when some are not protected."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        mock_branch1 = mock.MagicMock()
        mock_branch1.name = "main"
        mock_branch2 = mock.MagicMock()
        mock_branch2.name = "feature"

        mock_repo = mock.MagicMock()
        mock_repo.get_branches.return_value = [mock_branch1, mock_branch2]
        mock_branch1.get_protection.return_value = mock.MagicMock()
        mock_branch2.get_protection.side_effect = GithubException(
            404, {"message": "Not Found"}
        )

        mock_user.get_repo.return_value = mock_repo

        provider = GitHubProvider(token="ghp_test123")
        result = provider.get_protected_branches("owner", "repo")
        assert "main" in result
        assert "feature" not in result

    @mock.patch("lib.github_provider.Github")
    def test_get_protected_branches_api_error(self, mock_github_class):
        """Test getting protected branches with API error."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        mock_branch = mock.MagicMock()
        mock_branch.name = "main"
        mock_branch.get_protection.side_effect = GithubException(
            403, {"message": "Forbidden"}
        )

        mock_repo = mock.MagicMock()
        mock_repo.get_branches.return_value = [mock_branch]
        mock_user.get_repo.return_value = mock_repo

        provider = GitHubProvider(token="ghp_test123")
        with pytest.raises(GitHubProviderError):
            provider.get_protected_branches("owner", "repo")

    @mock.patch("lib.github_provider.Github")
    def test_get_issue_success(self, mock_github_class):
        """Test getting a GitHub issue."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        mock_issue = mock.MagicMock()
        mock_repo = mock.MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_user.get_repo.return_value = mock_repo

        provider = GitHubProvider(token="ghp_test123")
        result = provider.get_issue("owner", "repo", 123)
        assert result == mock_issue

    @mock.patch("lib.github_provider.Github")
    def test_get_issue_not_found(self, mock_github_class):
        """Test getting a GitHub issue that doesn't exist."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        mock_repo = mock.MagicMock()
        mock_repo.get_issue.side_effect = GithubException(
            404, {"message": "Not Found"}
        )
        mock_user.get_repo.return_value = mock_repo

        provider = GitHubProvider(token="ghp_test123")
        with pytest.raises(GitHubProviderError):
            provider.get_issue("owner", "repo", 999)

    @mock.patch("lib.github_provider.Github")
    def test_validate_issue_exists_true(self, mock_github_class):
        """Test validating existing issue."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        mock_repo = mock.MagicMock()
        mock_issue = mock.MagicMock()
        mock_repo.get_issue.return_value = mock_issue
        mock_user.get_repo.return_value = mock_repo

        provider = GitHubProvider(token="ghp_test123")
        result = provider.validate_issue_exists("owner", "repo", 123)
        assert result is True

    @mock.patch("lib.github_provider.Github")
    def test_validate_issue_exists_false(self, mock_github_class):
        """Test validating non-existing issue."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        mock_repo = mock.MagicMock()
        mock_repo.get_issue.side_effect = GithubException(
            404, {"message": "Not Found"}
        )
        mock_user.get_repo.return_value = mock_repo

        provider = GitHubProvider(token="ghp_test123")
        result = provider.validate_issue_exists("owner", "repo", 999)
        assert result is False

    @mock.patch("lib.github_provider.Github")
    def test_validate_branch_is_protected_true(self, mock_github_class):
        """Test validating protected branch."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        mock_branch = mock.MagicMock()
        mock_branch.get_protection.return_value = mock.MagicMock()
        mock_repo = mock.MagicMock()
        mock_repo.get_branch.return_value = mock_branch
        mock_user.get_repo.return_value = mock_repo

        provider = GitHubProvider(token="ghp_test123")
        result = provider.validate_branch_is_protected("owner", "repo", "main")
        assert result is True

    @mock.patch("lib.github_provider.Github")
    def test_validate_branch_is_protected_false(self, mock_github_class):
        """Test validating unprotected branch."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        mock_repo = mock.MagicMock()
        mock_repo.get_branch.side_effect = GithubException(
            404, {"message": "Not Found"}
        )
        mock_user.get_repo.return_value = mock_repo

        provider = GitHubProvider(token="ghp_test123")
        result = provider.validate_branch_is_protected(
            "owner", "repo", "feature"
        )
        assert result is False

    @mock.patch("lib.github_provider.Github")
    def test_validate_branch_is_protected_error(self, mock_github_class):
        """Test validating branch with API error."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        mock_repo = mock.MagicMock()
        mock_repo.get_branch.side_effect = GithubException(
            403, {"message": "Forbidden"}
        )
        mock_user.get_repo.return_value = mock_repo

        provider = GitHubProvider(token="ghp_test123")
        with pytest.raises(GitHubProviderError):
            provider.validate_branch_is_protected("owner", "repo", "main")

    @mock.patch("lib.github_provider.Github")
    def test_context_manager(self, mock_github_class):
        """Test using provider as context manager."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        with GitHubProvider(token="ghp_test123") as provider:
            assert provider.token == "ghp_test123"

    @mock.patch("lib.github_provider.Github")
    def test_close(self, mock_github_class):
        """Test closing the provider."""
        mock_client = mock.MagicMock()
        mock_github_class.return_value = mock_client
        mock_user = mock.MagicMock()
        mock_user.login = "testuser"
        mock_client.get_user.return_value = mock_user

        provider = GitHubProvider(token="ghp_test123")
        provider.close()  # Should not raise
