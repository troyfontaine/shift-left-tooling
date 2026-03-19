"""Configuration module for shift-left-tooling.

Handles environment variable loading, validation, and default values.
"""

import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ConfigDict,
    model_validator,
)

# Load environment variables from .env file if present
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class GitHubConfig(BaseModel):
    """GitHub API configuration."""

    token: Optional[str] = Field(
        default_factory=lambda: os.getenv("GITHUB_TOKEN"),
        description="GitHub personal access token",
    )
    api_url: str = Field(
        default="https://api.github.com",
        description="GitHub API base URL",
    )

    @field_validator("token", mode="after")
    @classmethod
    def validate_token_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate GitHub token format if provided."""
        if v and not v.startswith(("ghp_", "github_pat_")):
            logger.warning(
                "GitHub token may not be in the correct format. "
                "Tokens typically start with 'ghp_' or 'github_pat_'"
            )
        return v


class JiraConfig(BaseModel):
    """Jira API configuration."""

    url: Optional[str] = Field(
        default_factory=lambda: os.getenv("JIRA_URL"),
        description="Jira instance URL",
    )
    token: Optional[str] = Field(
        default_factory=lambda: os.getenv("JIRA_TOKEN"),
        description="Jira API token",
    )
    username: Optional[str] = Field(
        default_factory=lambda: os.getenv("JIRA_USERNAME"),
        description="Jira username (alternative to token)",
    )

    @model_validator(mode="after")
    def validate_url_format(self) -> "JiraConfig":
        """Validate Jira URL format if provided."""
        if self.url and not self.url.startswith(("http://", "https://")):
            raise ValueError("Jira URL must start with http:// or https://")
        return self


class BranchConfig(BaseModel):
    """Branch naming configuration."""

    naming_pattern: str = Field(
        default_factory=lambda: os.getenv(
            "BRANCH_NAMING_PATTERN", r"^[A-Z]+-\d+"
        ),
        description="Regex pattern for branch name validation",
    )

    @model_validator(mode="after")
    def validate_regex_pattern(self) -> "BranchConfig":
        """Validate regex pattern is valid."""
        try:
            re.compile(self.naming_pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e
        return self


class AppConfig(BaseModel):
    """Main application configuration."""

    model_config = ConfigDict(env_nested_delimiter="__")

    github: GitHubConfig = Field(default_factory=GitHubConfig)
    jira: JiraConfig = Field(default_factory=JiraConfig)
    branch: BranchConfig = Field(default_factory=BranchConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create AppConfig from environment variables."""
        return cls(
            github=GitHubConfig(),
            jira=JiraConfig(),
            branch=BranchConfig(),
        )


def get_config() -> AppConfig:
    """Get the current application configuration.

    Returns:
        AppConfig: The application configuration instance.
    """
    return AppConfig.from_env()
