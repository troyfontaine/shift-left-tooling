# Shift-Left Tooling

[![Build Status](https://github.com/troyfontaine/shift-left-tooling/actions/workflows/build-and-publish.yml/badge.svg)](https://github.com/troyfontaine/shift-left-tooling/actions/workflows/build-and-publish.yml)
[![Docker Hub](https://img.shields.io/docker/v/troyfontaine/shift-left-tooling)](https://hub.docker.com/r/troyfontaine/shift-left-tooling)

A Docker-based tooling suite for Git and Jira integration, designed to enforce shift-left practices through pre-commit hooks and CLI scripts. Provides branch protection, naming convention validation, Jira ticket linking, and changelog generation.

## Features

- 🔒 **Protected Branch Enforcement** - Prevent accidental pushes to protected branches
- 📝 **Branch Naming Validation** - Enforce consistent branch naming conventions
- 🎫 **Jira Integration** - Validate branches and commits reference valid Jira tickets
- 🐙 **GitHub Integration** - Query protected branches and validate GitHub issues
- 📋 **Changelog Generation** - Auto-generate changelogs from commit history
- 🪝 **Lefthook Integration** - Pre-commit, pre-push, and commit-msg hooks
- 🐳 **Docker-Ready** - Container image for consistent environments
- ✅ **CLI & Hook Modes** - Use as standalone CLI or automatic hooks

## Support Matrix

| Provider | Protected Branches | Branch/Issue Validation | Status |
|----------|-------------------|------------------------|--------|
| GitHub   | ✅ Full Support    | ✅ Full Support         | Stable |
| Jira     | N/A                | ✅ Full Support         | Stable |
| GitLab   | ❌ Not Implemented | ❌ Not Implemented      | Planned |
| Bitbucket| ❌ Not Implemented | ❌ Not Implemented      | Planned |

## Quick Start

### Using Docker

```bash
# Get protected branches
docker run \
  -v $(pwd)/.git:/app/.git:ro \
  -e GITHUB_TOKEN=ghp_xxxxxxxxxxxx \
  troyfontaine/shift-left-tooling:latest get-protected-branches

# Validate branch name
docker run \
  -e GITHUB_TOKEN=ghp_xxxxxxxxxxxx \
  -e JIRA_URL=https://jira.example.com \
  -e JIRA_TOKEN=xxxxxxxxxxxxxxxx \
  troyfontaine/shift-left-tooling:latest validate-branch-name PROJ-123-my-feature

# Generate changelog
docker run \
  -v $(pwd)/.git:/app/.git:ro \
  -e JIRA_URL=https://jira.example.com \
  -e JIRA_TOKEN=xxxxxxxxxxxxxxxx \
  troyfontaine/shift-left-tooling:latest generate-changelog --last-n-commits 10
```

### Using with Lefthook

Add to your workflow by installing [Lefthook](https://github.com/evilmartians/lefthook):

```bash
# Install lefthook
brew install lefthook  # or use your package manager

# Install hooks in your repo
lefthook install
```

Hooks will automatically run on:

- **Pre-commit**: Python linting (pylint, black, mypy) + branch naming validation
- **Pre-push**: Protected branch enforcement
- **Commit-msg**: Jira ticket link validation

## Scripts

### `get-protected-branches`

Query and list protected branches from your repository provider.

**Usage:**

```bash
docker run shift-left-tooling get-protected-branches [--json] [--provider PROVIDER]
```

**Options:**

- `--json` - Output as JSON instead of plain text
- `--provider` - Override provider detection (github, gitlab, bitbucket)

**Environment Variables:**

- `GITHUB_TOKEN` - Required for GitHub API access

**Example:**

```bash
docker run -e GITHUB_TOKEN=ghp_xxxx shift-left-tooling get-protected-branches --json
```

---

### `validate-branch-name`

Validate a branch name matches Jira ticket pattern (PROJ-123) or GitHub issue pattern (#123).

**Usage:**

```bash
docker run shift-left-tooling validate-branch-name BRANCH_NAME [--check-exists]
```

**Arguments:**

- `BRANCH_NAME` - The branch name to validate

**Options:**

- `--check-exists` - Verify the ticket/issue exists via API

**Environment Variables:**

- `GITHUB_TOKEN` - Required if checking GitHub issues
- `JIRA_URL` - Required if checking Jira tickets
- `JIRA_TOKEN` - Required if checking Jira tickets

**Example:**

```bash
docker run \
  -e GITHUB_TOKEN=ghp_xxxx \
  -e JIRA_URL=https://jira.example.com \
  -e JIRA_TOKEN=xxxx \
  shift-left-tooling validate-branch-name PROJ-123-feature --check-exists
```

---

### `enforce-protected-branches`

Prevent pushes to protected branches (intended as pre-push hook).

**Usage:**

```bash
docker run -v $(pwd)/.git:/app/.git:ro shift-left-tooling enforce-protected-branches
```

**Environment Variables:**

- `GITHUB_TOKEN` - Required for GitHub API access

**Example:**

```bash
# In pre-push hook
docker run -v $(pwd)/.git:/app/.git:ro -e GITHUB_TOKEN=ghp_xxxx shift-left-tooling enforce-protected-branches
```

Exit code: `0` if branch is not protected, `1` if protected or on error (fail-closed).

---

### `validate-branch-naming`

Validate current branch name follows configured naming pattern.

**Usage:**

```bash
docker run shift-left-tooling validate-branch-naming [BRANCH_NAME] [--pattern PATTERN]
```

**Arguments:**

- `BRANCH_NAME` - Branch to validate (defaults to current branch)

**Options:**

- `--pattern PATTERN` - Override the naming pattern (regex)

**Environment Variables:**

- `BRANCH_NAMING_PATTERN` - Default regex pattern for branch names
  - Default: `^[A-Z]+-\d+` (Jira format: PROJ-123)

**Example:**

```bash
docker run shift-left-tooling validate-branch-naming my-feature --pattern "^[a-z]+-.*"
```

---

### `validate-jira-commit-link`

Validate commit messages reference Jira tickets.

**Usage:**

```bash
docker run shift-left-tooling validate-jira-commit-link [--check-exists]
```

**Options:**

- `--check-exists` - Verify the ticket exists in Jira

**Environment Variables:**

- `JIRA_URL` - Jira instance URL
- `JIRA_TOKEN` - Jira API token

**Example:**

```bash
# As commit-msg hook
docker run \
  -e JIRA_URL=https://jira.example.com \
  -e JIRA_TOKEN=xxxx \
  shift-left-tooling validate-jira-commit-link --check-exists
```

Exit code: `0` if ticket found, `1` if not found or invalid.

---

### `generate-changelog`

Generate changelog from commit history.

**Usage:**

```bash
docker run shift-left-tooling generate-changelog [OPTIONS]
```

**Options:**

- `--last-n-commits N` - Include last N commits (default: 10)
- `--since-tag TAG` - Include commits since TAG
- `--tag-range TAG1 TAG2` - Include commits between two tags
- `--output FILE` - Write to file (default: stdout)
- `--format FORMAT` - Output format: markdown, json, or plain (default: markdown)

**Environment Variables:**

- `JIRA_URL` - Required for Jira ticket lookups
- `JIRA_TOKEN` - Required for Jira ticket lookups

**Example:**

```bash
docker run \
  -v $(pwd)/.git:/app/.git:ro \
  -e JIRA_URL=https://jira.example.com \
  -e JIRA_TOKEN=xxxx \
  shift-left-tooling generate-changelog --last-n-commits 50 --format markdown --output CHANGELOG.md
```

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GITHUB_TOKEN` | ✅ (GitHub) | GitHub personal access token | `ghp_xxxxxxxxxxxx` |
| `JIRA_URL` | ✅ (Jira) | Jira instance URL | `https://jira.example.com` |
| `JIRA_TOKEN` | ✅ (Jira) | Jira API token or password | `xxxxxxxxxxxxxxxx` |
| `BRANCH_NAMING_PATTERN` | ❌ | Regex for branch names | `^[A-Z]+-\d+` |
| `LOG_LEVEL` | ❌ | Logging level | `info` (debug, info, warning, error) |

### Obtaining Credentials

**GitHub Token:**

1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Create token with `repo` and `read:org` scopes
3. Copy and store securely

**Jira Token:**

1. Go to Jira Settings > Security > API tokens
2. Create API token
3. Use with username `automation` (default) or customize

## Installation

### Via Docker Hub

```bash
docker pull troyfontaine/shift-left-tooling:latest
```

### Local Development

```bash
# Clone repository
git clone https://github.com/troyfontaine/shift-left-tooling.git
cd shift-left-tooling

# Install dependencies
pip install -r requirements.txt

# Run scripts directly
python scripts/get_protected_branches.py

# Or use docker-compose
docker-compose run shift-left-tooling get-protected-branches
```

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed setup instructions.

## Configuration

### Override Via Environment Variables

```bash
# Use custom branch naming pattern
export BRANCH_NAMING_PATTERN='^feature-.*'

# Use custom logging level
export LOG_LEVEL=debug
```

### Docker Compose

Edit `docker-compose.yml` to set default environment variables:

```yaml
environment:
  GITHUB_TOKEN: "${GITHUB_TOKEN}"
  JIRA_URL: "${JIRA_URL}"
  JIRA_TOKEN: "${JIRA_TOKEN}"
  BRANCH_NAMING_PATTERN: "^[A-Z]+-\\d+"
  LOG_LEVEL: "info"
```

### Lefthook

Update `.lefthook.local.yml` to override behavior per developer:

```yaml
# .lefthook.local.yml (local override, not committed)
pre-commit:
  env:
    BRANCH_NAMING_PATTERN: "^[a-z]-.*"
    LOG_LEVEL: "debug"
```

## Architecture

```text
shift-left-tooling/
├── scripts/              # CLI entry points
│   ├── get_protected_branches.py
│   ├── validate_branch_name.py
│   ├── enforce_protected_branches.py
│   ├── validate_branch_naming.py
│   ├── validate_jira_commit_link.py
│   └── generate_changelog.py
├── lib/                  # Shared libraries
│   ├── config.py        # Config management
│   ├── git_utils.py     # Git operations
│   ├── github_provider.py   # GitHub API
│   └── jira_provider.py     # Jira API
├── tests/               # Unit tests
├── Dockerfile           # Docker image definition
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Local dev compose
└── README.md           # This file
```

## Development

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for:

- Local development setup
- Running tests
- Code style guidelines
- Contributing guidelines

## Testing

Run test suite:

```bash
# Using docker-compose
docker-compose run shift-left-tooling pytest tests/

# Locally (with environment configured)
pytest tests/ --cov=lib --cov=scripts --cov-report=html
```

Code coverage is enforced at 80% minimum.

## Linting & Type Checking

```bash
# Run all checks
docker-compose run shift-left-tooling sh -c "\
  black --check lib/ scripts/ && \
  pylint lib/ scripts/ && \
  mypy lib/ scripts/"

# Auto-fix formatting
docker-compose run shift-left-tooling black lib/ scripts/
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/PROJ-123-feature-name`)
3. Make your changes and commit with Jira ticket reference
4. Push to your fork
5. Open a pull request

## Support

- 📖 [Documentation](docs/DEVELOPMENT.md)
- 🐛 [Issues](https://github.com/troyfontaine/shift-left-tooling/issues)
- 💬 [Discussions](https://github.com/troyfontaine/shift-left-tooling/discussions)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

**Built with ❤️ for shift-left practices**
