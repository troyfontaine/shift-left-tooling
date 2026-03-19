"""Tests for config module."""

import os
from unittest import mock

import pytest

from lib.config import (
    AppConfig,
    BranchConfig,
    GitHubConfig,
    JiraConfig,
    get_config,
)


class TestGitHubConfig:
    """Tests for GitHubConfig."""

    def test_github_config_with_token(self):
        """Test GitHubConfig with valid token."""
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_test123"}):
            config = GitHubConfig()
            assert config.token == "ghp_test123"

    def test_github_config_without_token(self):
        """Test GitHubConfig without token."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = GitHubConfig()
            assert config.token is None


class TestJiraConfig:
    """Tests for JiraConfig."""

    def test_jira_config_with_url_and_token(self):
        """Test JiraConfig with URL and token."""
        with mock.patch.dict(
            os.environ,
            {
                "JIRA_URL": "https://jira.example.com",
                "JIRA_TOKEN": "test_token",
            },
        ):
            config = JiraConfig()
            assert config.url == "https://jira.example.com"
            assert config.token == "test_token"

    def test_jira_config_invalid_url(self):
        """Test JiraConfig with invalid URL."""
        with mock.patch.dict(os.environ, {"JIRA_URL": "invalid-url"}):
            with pytest.raises(ValueError):
                JiraConfig()


class TestBranchConfig:
    """Tests for BranchConfig."""

    def test_branch_config_default_pattern(self):
        """Test BranchConfig with default pattern."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = BranchConfig()
            assert config.naming_pattern == r"^[A-Z]+-\d+"

    def test_branch_config_custom_pattern(self):
        """Test BranchConfig with custom pattern."""
        with mock.patch.dict(
            os.environ, {"BRANCH_NAMING_PATTERN": r"^feature-.*"}
        ):
            config = BranchConfig()
            assert config.naming_pattern == r"^feature-.*"

    def test_branch_config_invalid_pattern(self):
        """Test BranchConfig with invalid regex pattern."""
        with mock.patch.dict(
            os.environ, {"BRANCH_NAMING_PATTERN": "[invalid(regex"}
        ):
            with pytest.raises(ValueError):
                BranchConfig()


class TestAppConfig:
    """Tests for AppConfig."""

    def test_app_config_from_env(self):
        """Test AppConfig.from_env()."""
        config = AppConfig.from_env()
        assert isinstance(config.github, GitHubConfig)
        assert isinstance(config.jira, JiraConfig)
        assert isinstance(config.branch, BranchConfig)

    def test_get_config(self):
        """Test get_config() function."""
        config = get_config()
        assert isinstance(config, AppConfig)
