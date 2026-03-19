"""Tests for git_utils module."""

import os
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from lib.git_utils import (
    GitProvider,
    GitProviderError,
    detect_provider,
    extract_github_issue_from_message,
    extract_jira_ticket_from_message,
    extract_owner_repo,
    get_current_branch,
    get_git_origin,
    get_git_root,
)


class TestGetGitRoot:
    """Tests for get_git_root function."""

    def test_get_git_root_success(self):
        """Test successfully getting git root."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(stdout="/home/user/repo\n")
            result = get_git_root()
            assert result == Path("/home/user/repo")

    def test_get_git_root_failure(self):
        """Test get_git_root when not in git repo."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, "git")
            with pytest.raises(GitProviderError):
                get_git_root()


class TestGetGitOrigin:
    """Tests for get_git_origin function."""

    def test_get_git_origin_success(self):
        """Test successfully getting git origin."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(
                stdout="https://github.com/user/repo.git\n"
            )
            result = get_git_origin()
            assert result == "https://github.com/user/repo.git"

    def test_get_git_origin_empty(self):
        """Test get_git_origin when no origin configured."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(stdout="")
            with pytest.raises(GitProviderError):
                get_git_origin()


class TestDetectProvider:
    """Tests for detect_provider function."""

    def test_detect_provider_github_https(self):
        """Test detecting GitHub from HTTPS URL."""
        result = detect_provider("https://github.com/user/repo.git")
        assert result == GitProvider.GITHUB

    def test_detect_provider_github_ssh(self):
        """Test detecting GitHub from SSH URL."""
        result = detect_provider("git@github.com:user/repo.git")
        assert result == GitProvider.GITHUB

    def test_detect_provider_gitlab(self):
        """Test detecting GitLab."""
        result = detect_provider("https://gitlab.com/user/repo.git")
        assert result == GitProvider.GITLAB

    def test_detect_provider_bitbucket(self):
        """Test detecting Bitbucket."""
        result = detect_provider("https://bitbucket.org/user/repo.git")
        assert result == GitProvider.BITBUCKET

    def test_detect_provider_unknown(self):
        """Test detecting unknown provider."""
        result = detect_provider("https://gitea.example.com/user/repo.git")
        assert result == GitProvider.UNKNOWN


class TestExtractOwnerRepo:
    """Tests for extract_owner_repo function."""

    def test_extract_owner_repo_https(self):
        """Test extracting owner/repo from HTTPS URL."""
        owner, repo = extract_owner_repo("https://github.com/myuser/myrepo.git")
        assert owner == "myuser"
        assert repo == "myrepo"

    def test_extract_owner_repo_ssh(self):
        """Test extracting owner/repo from SSH URL."""
        owner, repo = extract_owner_repo("git@github.com:myuser/myrepo.git")
        assert owner == "myuser"
        assert repo == "myrepo"

    def test_extract_owner_repo_https_no_git_suffix(self):
        """Test extracting owner/repo from HTTPS URL without .git."""
        owner, repo = extract_owner_repo("https://github.com/myuser/myrepo")
        assert owner == "myuser"
        assert repo == "myrepo"

    def test_extract_owner_repo_invalid_format(self):
        """Test extracting from invalid URL format."""
        with pytest.raises(GitProviderError):
            extract_owner_repo("invalid-url-format")


class TestGetCurrentBranch:
    """Tests for get_current_branch function."""

    def test_get_current_branch_success(self):
        """Test successfully getting current branch."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.MagicMock(stdout="main\n")
            result = get_current_branch()
            assert result == "main"


class TestExtractJiraTicket:
    """Tests for extract_jira_ticket_from_message function."""

    def test_extract_jira_ticket_success(self):
        """Test successfully extracting Jira ticket."""
        message = "PROJ-123: Implement new feature"
        result = extract_jira_ticket_from_message(message)
        assert result == "PROJ-123"

    def test_extract_jira_ticket_multiple_formats(self):
        """Test extracting various Jira formats."""
        message = "Fix bug references MYAPP-456 in the code"
        result = extract_jira_ticket_from_message(message)
        assert result == "MYAPP-456"

    def test_extract_jira_ticket_not_found(self):
        """Test when no Jira ticket found."""
        message = "This is a commit message without ticket"
        result = extract_jira_ticket_from_message(message)
        assert result is None


class TestExtractGithubIssue:
    """Tests for extract_github_issue_from_message function."""

    def test_extract_github_issue_success(self):
        """Test successfully extracting GitHub issue."""
        message = "Fixes #123: Implement feature"
        result = extract_github_issue_from_message(message)
        assert result == "123"

    def test_extract_github_issue_not_found(self):
        """Test when no GitHub issue found."""
        message = "This is a commit message without issue"
        result = extract_github_issue_from_message(message)
        assert result is None
