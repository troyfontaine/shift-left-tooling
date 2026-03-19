"""Tests for scripts module."""

from unittest import mock
import sys
import json

import pytest

from scripts.validate_branch_name import (
    validate_github_pattern,
    validate_jira_pattern,
    check_jira_ticket_exists,
    check_github_issue_exists,
    main as validate_branch_name_main,
)
from scripts.validate_branch_naming import validate_branch_naming, main as validate_branch_naming_main
from scripts.get_protected_branches import (
    get_protected_branches_github,
    get_protected_branches_gitlab,
    get_protected_branches_bitbucket,
    main as get_protected_branches_main,
)
from scripts.enforce_protected_branches import main as enforce_protected_branches_main
from scripts.validate_jira_commit_link import main as validate_jira_commit_link_main
from scripts.generate_changelog import (
    get_commits_in_range,
    get_ticket_info_from_jira,
    generate_markdown_changelog,
    generate_json_changelog,
    generate_plain_changelog,
    main as generate_changelog_main,
)
from lib.git_utils import GitProviderError, GitProvider
from lib.github_provider import GitHubProviderError


class TestValidateBranchName:
    """Tests for validate_branch_name script."""

    def test_validate_jira_pattern_success(self):
        """Test validating Jira pattern."""
        result = validate_jira_pattern("PROJ-123-feature")
        assert result == "PROJ-123"

    def test_validate_jira_pattern_failure(self):
        """Test when Jira pattern not found."""
        result = validate_jira_pattern("feature-branch")
        assert result is None

    def test_validate_github_pattern_success(self):
        """Test validating GitHub pattern."""
        # Test lowercase 'gh' with digits
        result = validate_github_pattern("gh123")
        assert result == "123"

        # Test uppercase 'GH' with digits
        result = validate_github_pattern("GH456")
        assert result == "456"

        # Test 'gh-' variant with dash
        result = validate_github_pattern("gh-789")
        assert result == "789"

        # Test 'GH-' variant with dash
        result = validate_github_pattern("GH-123")
        assert result == "123"

        # Test 'gh' in middle of branch name
        result = validate_github_pattern("feature-gh999")
        assert result == "999"

    def test_validate_github_pattern_failure(self):
        """Test when GitHub pattern not found."""
        result = validate_github_pattern("feature-branch")
        assert result is None

        # Verify old '#' pattern no longer works
        result = validate_github_pattern("feature-#456")
        assert result is None

    @mock.patch("scripts.validate_branch_name.JiraProvider")
    def test_check_jira_ticket_exists_success(self, mock_jira):
        """Test checking if Jira ticket exists."""
        mock_provider = mock.MagicMock()
        mock_provider.validate_ticket_exists.return_value = True
        mock_jira.return_value.__enter__.return_value = mock_provider

        result = check_jira_ticket_exists("PROJ-123")
        assert result is True

    @mock.patch("scripts.validate_branch_name.JiraProvider")
    def test_check_jira_ticket_exists_failure(self, mock_jira):
        """Test when Jira ticket doesn't exist."""
        mock_provider = mock.MagicMock()
        mock_provider.validate_ticket_exists.return_value = False
        mock_jira.return_value.__enter__.return_value = mock_provider

        result = check_jira_ticket_exists("PROJ-999")
        assert result is False

    @mock.patch("scripts.validate_branch_name.GitHubProvider")
    @mock.patch("scripts.validate_branch_name.get_git_origin")
    @mock.patch("scripts.validate_branch_name.extract_owner_repo")
    def test_check_github_issue_exists_success(self, mock_extract, mock_origin, mock_github):
        """Test checking if GitHub issue exists."""
        mock_origin.return_value = "git@github.com:owner/repo.git"
        mock_extract.return_value = ("owner", "repo")
        mock_provider = mock.MagicMock()
        mock_provider.validate_issue_exists.return_value = True
        mock_github.return_value.__enter__.return_value = mock_provider

        result = check_github_issue_exists("123")
        assert result is True

    @mock.patch("scripts.validate_branch_name.GitHubProvider")
    @mock.patch("scripts.validate_branch_name.get_git_origin")
    @mock.patch("scripts.validate_branch_name.extract_owner_repo")
    def test_check_github_issue_exists_error(self, mock_extract, mock_origin, mock_github):
        """Test error handling when checking GitHub."""
        mock_origin.side_effect = GitProviderError("Git error")
        result = check_github_issue_exists("123")
        assert result is False

    @mock.patch("scripts.validate_branch_name.sys.argv", ["validate_branch_name.py", "PROJ-123"])
    @mock.patch("scripts.validate_branch_name.validate_jira_pattern")
    def test_main_valid_jira_ticket(self, mock_validate):
        """Test main with valid jira ticket."""
        mock_validate.return_value = "PROJ-123"
        result = validate_branch_name_main()
        assert result == 0

    @mock.patch("scripts.validate_branch_name.sys.argv", ["validate_branch_name.py", "feature"])
    @mock.patch("scripts.validate_branch_name.validate_jira_pattern")
    @mock.patch("scripts.validate_branch_name.validate_github_pattern")
    def test_main_invalid_branch_name(self, mock_github, mock_jira):
        """Test main with invalid branch name."""
        mock_jira.return_value = None
        mock_github.return_value = None
        result = validate_branch_name_main()
        assert result == 1

    @mock.patch("scripts.validate_branch_name.sys.argv", ["validate_branch_name.py", "gh123"])
    @mock.patch("scripts.validate_branch_name.validate_jira_pattern")
    @mock.patch("scripts.validate_branch_name.validate_github_pattern")
    def test_main_valid_github_issue(self, mock_github, mock_jira):
        """Test main with valid GitHub issue."""
        mock_jira.return_value = None
        mock_github.return_value = "123"
        result = validate_branch_name_main()
        assert result == 0


class TestValidateBranchNaming:
    """Tests for validate_branch_naming script."""

    def test_validate_branch_naming_success(self):
        """Test validating branch name against pattern."""
        result = validate_branch_naming("PROJ-123", r"^[A-Z]+-\d+")
        assert result is True

    def test_validate_branch_naming_failure(self):
        """Test branch name that doesn't match pattern."""
        result = validate_branch_naming("feature-branch", r"^[A-Z]+-\d+")
        assert result is False

    def test_validate_branch_naming_invalid_pattern(self):
        """Test with invalid regex pattern."""
        result = validate_branch_naming("test", "[invalid(")
        assert result is False

    @mock.patch("scripts.validate_branch_naming.sys.argv", ["validate_branch_naming.py", "PROJ-123"])
    @mock.patch("scripts.validate_branch_naming.get_config")
    def test_main_valid_branch(self, mock_config):
        """Test main with valid branch name."""
        mock_config.return_value.branch.naming_pattern = r"^[A-Z]+-\d+"
        result = validate_branch_naming_main()
        assert result == 0

    @mock.patch("scripts.validate_branch_naming.sys.argv", ["validate_branch_naming.py", "feature"])
    @mock.patch("scripts.validate_branch_naming.get_config")
    def test_main_invalid_branch(self, mock_config):
        """Test main with invalid branch name."""
        mock_config.return_value.branch.naming_pattern = r"^[A-Z]+-\d+"
        result = validate_branch_naming_main()
        assert result == 1

    @mock.patch("scripts.validate_branch_naming.sys.argv", ["validate_branch_naming.py"])
    @mock.patch("scripts.validate_branch_naming.get_current_branch")
    @mock.patch("scripts.validate_branch_naming.get_config")
    def test_main_current_branch_valid(self, mock_config, mock_get_branch):
        """Test main using current branch."""
        mock_get_branch.return_value = "PROJ-123"
        mock_config.return_value.branch.naming_pattern = r"^[A-Z]+-\d+"
        result = validate_branch_naming_main()
        assert result == 0

    @mock.patch("scripts.validate_branch_naming.sys.argv", ["validate_branch_naming.py"])
    @mock.patch("scripts.validate_branch_naming.get_current_branch")
    def test_main_get_branch_error(self, mock_get_branch):
        """Test main when getting current branch fails."""
        mock_get_branch.side_effect = GitProviderError("Git error")
        result = validate_branch_naming_main()
        assert result == 1


class TestGetProtectedBranches:
    """Tests for get_protected_branches script."""

    @mock.patch("scripts.get_protected_branches.GitHubProvider")
    def test_get_protected_branches_github(self, mock_github_class):
        """Test getting GitHub protected branches."""
        mock_provider = mock.MagicMock()
        mock_provider.get_protected_branches.return_value = ["main", "develop"]
        mock_github_class.return_value.__enter__.return_value = mock_provider

        result = get_protected_branches_github("owner", "repo")
        assert result == ["main", "develop"]

    @mock.patch("scripts.get_protected_branches.GitLabProvider")
    def test_get_protected_branches_gitlab(self, mock_gitlab_class):
        """Test getting GitLab protected branches."""
        mock_provider = mock.MagicMock()
        mock_provider.get_protected_branches.return_value = ["main"]
        mock_gitlab_class.return_value = mock_provider

        result = get_protected_branches_gitlab("owner", "repo")
        assert result == ["main"]

    @mock.patch("scripts.get_protected_branches.BitbucketProvider")
    def test_get_protected_branches_bitbucket(self, mock_bitbucket_class):
        """Test getting Bitbucket protected branches."""
        mock_provider = mock.MagicMock()
        mock_provider.get_protected_branches.return_value = ["main"]
        mock_bitbucket_class.return_value = mock_provider

        result = get_protected_branches_bitbucket("owner", "repo")
        assert result == ["main"]

    @mock.patch("scripts.get_protected_branches.sys.argv", ["get_protected_branches.py"])
    @mock.patch("scripts.get_protected_branches.get_git_origin")
    @mock.patch("scripts.get_protected_branches.extract_owner_repo")
    @mock.patch("scripts.get_protected_branches.detect_provider")
    @mock.patch("scripts.get_protected_branches.get_protected_branches_github")
    def test_main_github_success(self, mock_get_branches, mock_detect, mock_extract, mock_origin):
        """Test main with GitHub provider."""
        mock_origin.return_value = "git@github.com:owner/repo.git"
        mock_extract.return_value = ("owner", "repo")
        mock_detect.return_value = GitProvider.GITHUB
        mock_get_branches.return_value = ["main"]

        result = get_protected_branches_main()
        assert result == 0

    @mock.patch("scripts.get_protected_branches.sys.argv", ["get_protected_branches.py", "--json"])
    @mock.patch("scripts.get_protected_branches.get_git_origin")
    @mock.patch("scripts.get_protected_branches.extract_owner_repo")
    @mock.patch("scripts.get_protected_branches.detect_provider")
    @mock.patch("scripts.get_protected_branches.get_protected_branches_github")
    def test_main_json_output(self, mock_get_branches, mock_detect, mock_extract, mock_origin):
        """Test main with JSON output."""
        mock_origin.return_value = "git@github.com:owner/repo.git"
        mock_extract.return_value = ("owner", "repo")
        mock_detect.return_value = GitProvider.GITHUB
        mock_get_branches.return_value = ["main"]

        result = get_protected_branches_main()
        assert result == 0

    @mock.patch("scripts.get_protected_branches.sys.argv", ["get_protected_branches.py"])
    @mock.patch("scripts.get_protected_branches.get_git_origin")
    def test_main_git_error(self, mock_origin):
        """Test main with git error."""
        mock_origin.side_effect = GitProviderError("Git error")
        result = get_protected_branches_main()
        assert result == 1

    @mock.patch("scripts.get_protected_branches.sys.argv", ["get_protected_branches.py"])
    @mock.patch("scripts.get_protected_branches.get_git_origin")
    @mock.patch("scripts.get_protected_branches.extract_owner_repo")
    @mock.patch("scripts.get_protected_branches.detect_provider")
    def test_main_unknown_provider(self, mock_detect, mock_extract, mock_origin):
        """Test main with unknown provider."""
        mock_origin.return_value = "git@bitbucket.org:owner/repo.git"
        mock_extract.return_value = ("owner", "repo")
        mock_detect.return_value = "unknown"

        result = get_protected_branches_main()
        assert result == 1

    @mock.patch("scripts.get_protected_branches.sys.argv", ["get_protected_branches.py", "--provider", "github"])
    @mock.patch("scripts.get_protected_branches.get_git_origin")
    @mock.patch("scripts.get_protected_branches.extract_owner_repo")
    @mock.patch("scripts.get_protected_branches.get_protected_branches_github")
    def test_main_provider_override(self, mock_get_branches, mock_extract, mock_origin):
        """Test main with provider override."""
        mock_origin.return_value = "git@github.com:owner/repo.git"
        mock_extract.return_value = ("owner", "repo")
        mock_get_branches.return_value = ["main"]

        result = get_protected_branches_main()
        assert result == 0


class TestEnforceProtectedBranches:
    """Tests for enforce_protected_branches script."""

    @mock.patch("scripts.enforce_protected_branches.sys.argv", ["enforce_protected_branches.py"])
    @mock.patch("scripts.enforce_protected_branches.get_current_branch")
    @mock.patch("scripts.enforce_protected_branches.get_git_origin")
    @mock.patch("scripts.enforce_protected_branches.extract_owner_repo")
    @mock.patch("scripts.enforce_protected_branches.detect_provider")
    @mock.patch("scripts.enforce_protected_branches.GitHubProvider")
    def test_main_branch_not_protected(self, mock_github_class, mock_detect, mock_extract, mock_origin, mock_get_branch):
        """Test main when branch is not protected."""
        mock_get_branch.return_value = "feature-123"
        mock_origin.return_value = "git@github.com:owner/repo.git"
        mock_extract.return_value = ("owner", "repo")
        mock_detect.return_value = GitProvider.GITHUB
        mock_provider = mock.MagicMock()
        mock_provider.get_protected_branches.return_value = ["main", "develop"]
        mock_github_class.return_value.__enter__.return_value = mock_provider

        result = enforce_protected_branches_main()
        assert result == 0

    @mock.patch("scripts.enforce_protected_branches.sys.argv", ["enforce_protected_branches.py"])
    @mock.patch("scripts.enforce_protected_branches.get_current_branch")
    @mock.patch("scripts.enforce_protected_branches.get_git_origin")
    @mock.patch("scripts.enforce_protected_branches.extract_owner_repo")
    @mock.patch("scripts.enforce_protected_branches.detect_provider")
    @mock.patch("scripts.enforce_protected_branches.GitHubProvider")
    def test_main_branch_protected(self, mock_github_class, mock_detect, mock_extract, mock_origin, mock_get_branch):
        """Test main when branch is protected."""
        mock_get_branch.return_value = "main"
        mock_origin.return_value = "git@github.com:owner/repo.git"
        mock_extract.return_value = ("owner", "repo")
        mock_detect.return_value = GitProvider.GITHUB
        mock_provider = mock.MagicMock()
        mock_provider.get_protected_branches.return_value = ["main", "develop"]
        mock_github_class.return_value.__enter__.return_value = mock_provider

        result = enforce_protected_branches_main()
        assert result == 1

    @mock.patch("scripts.enforce_protected_branches.sys.argv", ["enforce_protected_branches.py"])
    @mock.patch("scripts.enforce_protected_branches.get_current_branch")
    @mock.patch("scripts.enforce_protected_branches.get_git_origin")
    @mock.patch("scripts.enforce_protected_branches.extract_owner_repo")
    @mock.patch("scripts.enforce_protected_branches.detect_provider")
    def test_main_unsupported_provider(self, mock_detect, mock_extract, mock_origin, mock_get_branch):
        """Test main with unsupported provider."""
        mock_get_branch.return_value = "feature"
        mock_origin.return_value = "git@gitlab.com:owner/repo.git"
        mock_extract.return_value = ("owner", "repo")
        mock_detect.return_value = GitProvider.GITLAB

        result = enforce_protected_branches_main()
        assert result == 0

    @mock.patch("scripts.enforce_protected_branches.sys.argv", ["enforce_protected_branches.py"])
    @mock.patch("scripts.enforce_protected_branches.get_current_branch")
    def test_main_git_error(self, mock_get_branch):
        """Test main with git error."""
        mock_get_branch.side_effect = GitProviderError("Git error")
        result = enforce_protected_branches_main()
        assert result == 0


class TestValidateJiraCommitLink:
    """Tests for validate_jira_commit_link script."""

    @mock.patch("scripts.validate_jira_commit_link.sys.argv", ["validate_jira_commit_link.py"])
    @mock.patch("scripts.validate_jira_commit_link.get_commit_message")
    @mock.patch("scripts.validate_jira_commit_link.extract_jira_ticket_from_message")
    def test_main_valid_ticket(self, mock_extract, mock_get_message):
        """Test main with valid Jira ticket."""
        mock_get_message.return_value = "PROJ-123: Fix bug"
        mock_extract.return_value = "PROJ-123"

        result = validate_jira_commit_link_main()
        assert result == 0

    @mock.patch("scripts.validate_jira_commit_link.sys.argv", ["validate_jira_commit_link.py"])
    @mock.patch("scripts.validate_jira_commit_link.get_commit_message")
    @mock.patch("scripts.validate_jira_commit_link.extract_jira_ticket_from_message")
    def test_main_missing_ticket(self, mock_extract, mock_get_message):
        """Test main without ticket reference."""
        mock_get_message.return_value = "Fix bug"
        mock_extract.return_value = None

        result = validate_jira_commit_link_main()
        assert result == 1

    @mock.patch("scripts.validate_jira_commit_link.sys.argv", ["validate_jira_commit_link.py", "--check-exists"])
    @mock.patch("scripts.validate_jira_commit_link.get_commit_message")
    @mock.patch("scripts.validate_jira_commit_link.extract_jira_ticket_from_message")
    @mock.patch("scripts.validate_jira_commit_link.JiraProvider")
    def test_main_check_exists_valid(self, mock_jira_class, mock_extract, mock_get_message):
        """Test main with --check-exists for valid ticket."""
        mock_get_message.return_value = "PROJ-123: Fix bug"
        mock_extract.return_value = "PROJ-123"
        mock_provider = mock.MagicMock()
        mock_provider.validate_ticket_exists.return_value = True
        mock_jira_class.return_value.__enter__.return_value = mock_provider

        result = validate_jira_commit_link_main()
        assert result == 0

    @mock.patch("scripts.validate_jira_commit_link.sys.argv", ["validate_jira_commit_link.py", "--check-exists"])
    @mock.patch("scripts.validate_jira_commit_link.get_commit_message")
    @mock.patch("scripts.validate_jira_commit_link.extract_jira_ticket_from_message")
    @mock.patch("scripts.validate_jira_commit_link.JiraProvider")
    def test_main_check_exists_invalid(self, mock_jira_class, mock_extract, mock_get_message):
        """Test main with --check-exists for invalid ticket."""
        mock_get_message.return_value = "PROJ-999: Fix bug"
        mock_extract.return_value = "PROJ-999"
        mock_provider = mock.MagicMock()
        mock_provider.validate_ticket_exists.return_value = False
        mock_jira_class.return_value.__enter__.return_value = mock_provider

        result = validate_jira_commit_link_main()
        assert result == 1

    @mock.patch("scripts.validate_jira_commit_link.sys.argv", ["validate_jira_commit_link.py", "--check-exists"])
    @mock.patch("scripts.validate_jira_commit_link.get_commit_message")
    @mock.patch("scripts.validate_jira_commit_link.extract_jira_ticket_from_message")
    @mock.patch("scripts.validate_jira_commit_link.JiraProvider")
    def test_main_check_exists_error(self, mock_jira_class, mock_extract, mock_get_message):
        """Test main with --check-exists when verification fails."""
        mock_get_message.return_value = "PROJ-123: Fix bug"
        mock_extract.return_value = "PROJ-123"
        mock_jira_class.return_value.__enter__.side_effect = Exception("Jira error")

        result = validate_jira_commit_link_main()
        assert result == 1

    @mock.patch("scripts.validate_jira_commit_link.sys.argv", ["validate_jira_commit_link.py"])
    @mock.patch("scripts.validate_jira_commit_link.get_commit_message")
    def test_main_git_error(self, mock_get_message):
        """Test main with git error."""
        mock_get_message.side_effect = GitProviderError("Git error")
        result = validate_jira_commit_link_main()
        assert result == 1


class TestGenerateChangelog:
    """Tests for generate_changelog script."""

    @mock.patch("scripts.generate_changelog.get_commit_history")
    def test_get_commits_in_range_default(self, mock_get_history):
        """Test getting commits with default limit."""
        mock_get_history.return_value = ["abc123", "def456"]
        result = get_commits_in_range(limit=10)
        assert result == ["abc123", "def456"]

    @mock.patch("scripts.generate_changelog.get_commit_history")
    def test_get_commits_in_range_with_tag(self, mock_get_history):
        """Test getting commits since tag."""
        mock_get_history.return_value = ["abc123"]
        result = get_commits_in_range(since_tag="v1.0", limit=5)
        assert result == ["abc123"]

    @mock.patch("scripts.generate_changelog.JiraProvider")
    def test_get_ticket_info_from_jira_success(self, mock_jira_class):
        """Test getting ticket info from Jira."""
        mock_provider = mock.MagicMock()
        mock_issue = mock.MagicMock()
        mock_issue.fields.summary = "Fix bug"
        mock_issue.permalink.return_value = "https://jira.example.com/browse/PROJ-123"
        mock_provider.get_ticket.return_value = mock_issue
        mock_provider.get_ticket_status.return_value = "DONE"
        mock_jira_class.return_value.__enter__.return_value = mock_provider

        result = get_ticket_info_from_jira("PROJ-123")
        assert result is not None
        assert result["key"] == "PROJ-123"
        assert result["summary"] == "Fix bug"
        assert result["status"] == "DONE"

    @mock.patch("scripts.generate_changelog.JiraProvider")
    def test_get_ticket_info_from_jira_not_found(self, mock_jira_class):
        """Test when ticket not found in Jira."""
        mock_provider = mock.MagicMock()
        from lib.jira_provider import JiraProviderError
        mock_provider.get_ticket.side_effect = JiraProviderError("Not found")
        mock_jira_class.return_value.__enter__.return_value = mock_provider

        result = get_ticket_info_from_jira("PROJ-999")
        assert result is None

    def test_generate_markdown_changelog_empty(self):
        """Test generating markdown changelog with no tickets."""
        result = generate_markdown_changelog({})
        assert "No tickets found" in result

    def test_generate_markdown_changelog_with_tickets(self):
        """Test generating markdown changelog with tickets."""
        tickets = {
            "PROJ-123": {
                "summary": "Fix bug",
                "status": "DONE"
            }
        }
        result = generate_markdown_changelog(tickets)
        assert "# Changelog" in result
        assert "PROJ-123" in result
        assert "Fix bug" in result

    def test_generate_json_changelog_empty(self):
        """Test generating JSON changelog with no tickets."""
        result = generate_json_changelog({})
        assert result == "{}"

    def test_generate_json_changelog_with_tickets(self):
        """Test generating JSON changelog with tickets."""
        tickets = {
            "PROJ-123": {
                "summary": "Fix bug",
                "status": "DONE"
            }
        }
        result = generate_json_changelog(tickets)
        parsed = json.loads(result)
        assert "PROJ-123" in parsed

    def test_generate_plain_changelog_empty(self):
        """Test generating plain text changelog with no tickets."""
        result = generate_plain_changelog({})
        assert "No tickets found" in result

    def test_generate_plain_changelog_with_tickets(self):
        """Test generating plain text changelog with tickets."""
        tickets = {
            "PROJ-123": {
                "summary": "Fix bug"
            }
        }
        result = generate_plain_changelog(tickets)
        assert "CHANGELOG" in result
        assert "PROJ-123" in result

    @mock.patch("scripts.generate_changelog.sys.argv", ["generate_changelog.py"])
    @mock.patch("scripts.generate_changelog.get_commits_in_range")
    def test_main_default_format(self, mock_get_commits):
        """Test main with default markdown format."""
        mock_get_commits.return_value = []
        result = generate_changelog_main()
        assert result == 0

    @mock.patch("scripts.generate_changelog.sys.argv", ["generate_changelog.py", "--format", "json"])
    @mock.patch("scripts.generate_changelog.get_commits_in_range")
    def test_main_json_format(self, mock_get_commits):
        """Test main with JSON format."""
        mock_get_commits.return_value = []
        result = generate_changelog_main()
        assert result == 0

    @mock.patch("scripts.generate_changelog.sys.argv", ["generate_changelog.py", "--format", "plain"])
    @mock.patch("scripts.generate_changelog.get_commits_in_range")
    def test_main_plain_format(self, mock_get_commits):
        """Test main with plain text format."""
        mock_get_commits.return_value = []
        result = generate_changelog_main()
        assert result == 0

    @mock.patch("scripts.generate_changelog.sys.argv",
                ["generate_changelog.py", "--last-n-commits", "20"])
    @mock.patch("scripts.generate_changelog.get_commits_in_range")
    def test_main_custom_commit_count(self, mock_get_commits):
        """Test main with custom commit count."""
        mock_get_commits.return_value = []
        result = generate_changelog_main()
        assert result == 0

    @mock.patch("scripts.generate_changelog.sys.argv",
                ["generate_changelog.py", "--output", "/tmp/changelog.md"])
    @mock.patch("scripts.generate_changelog.get_commits_in_range")
    @mock.patch("builtins.open", mock.mock_open())
    def test_main_output_file(self, mock_get_commits):
        """Test main writing to output file."""
        mock_get_commits.return_value = []
        result = generate_changelog_main()
        assert result == 0

    @mock.patch("scripts.generate_changelog.sys.argv", ["generate_changelog.py"])
    @mock.patch("scripts.generate_changelog.get_commits_in_range")
    def test_main_git_error(self, mock_get_commits):
        """Test main with git error."""
        mock_get_commits.side_effect = GitProviderError("Git error")
        result = generate_changelog_main()
        assert result == 1

    @mock.patch("scripts.generate_changelog.sys.argv", ["generate_changelog.py"])
    @mock.patch("scripts.generate_changelog.get_commits_in_range")
    def test_main_unexpected_error(self, mock_get_commits):
        """Test main with unexpected error."""
        mock_get_commits.side_effect = Exception("Unexpected error")
        result = generate_changelog_main()
        assert result == 1


class TestValidateBranchNameMain:
    """Additional tests for validate_branch_name main function."""

    @mock.patch("scripts.validate_branch_name.sys.argv",
                ["validate_branch_name.py", "PROJ-123", "--check-exists"])
    @mock.patch("scripts.validate_branch_name.validate_jira_pattern")
    @mock.patch("scripts.validate_branch_name.check_jira_ticket_exists")
    def test_main_jira_check_exists_valid(self, mock_check, mock_validate):
        """Test main checking if Jira ticket exists - valid."""
        mock_validate.return_value = "PROJ-123"
        mock_check.return_value = True
        result = validate_branch_name_main()
        assert result == 0

    @mock.patch("scripts.validate_branch_name.sys.argv",
                ["validate_branch_name.py", "PROJ-123", "--check-exists"])
    @mock.patch("scripts.validate_branch_name.validate_jira_pattern")
    @mock.patch("scripts.validate_branch_name.check_jira_ticket_exists")
    def test_main_jira_check_exists_invalid(self, mock_check, mock_validate):
        """Test main checking if Jira ticket exists - invalid."""
        mock_validate.return_value = "PROJ-999"
        mock_check.return_value = False
        result = validate_branch_name_main()
        assert result == 1

    @mock.patch("scripts.validate_branch_name.sys.argv",
                ["validate_branch_name.py", "gh123", "--check-exists"])
    @mock.patch("scripts.validate_branch_name.validate_jira_pattern")
    @mock.patch("scripts.validate_branch_name.validate_github_pattern")
    @mock.patch("scripts.validate_branch_name.check_github_issue_exists")
    def test_main_github_check_exists_valid(self, mock_check, mock_github, mock_jira):
        """Test main checking if GitHub issue exists - valid."""
        mock_jira.return_value = None
        mock_github.return_value = "123"
        mock_check.return_value = True
        result = validate_branch_name_main()
        assert result == 0

    @mock.patch("scripts.validate_branch_name.sys.argv",
                ["validate_branch_name.py", "gh123", "--check-exists"])
    @mock.patch("scripts.validate_branch_name.validate_jira_pattern")
    @mock.patch("scripts.validate_branch_name.validate_github_pattern")
    @mock.patch("scripts.validate_branch_name.check_github_issue_exists")
    def test_main_github_check_exists_invalid(self, mock_check, mock_github, mock_jira):
        """Test main checking if GitHub issue exists - invalid."""
        mock_jira.return_value = None
        mock_github.return_value = "999"
        mock_check.return_value = False
        result = validate_branch_name_main()
        assert result == 1
