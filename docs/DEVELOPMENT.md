# Development Guide

This guide contains setup and development instructions for the shift-left-tooling project.

## Prerequisites

- Docker and Docker Compose
- Python 3.12 (for local development)
- Git
- Lefthook (optional, for local pre-commit hooks)

## Local Setup

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/troyfontaine/shift-left-tooling.git
cd shift-left-tooling

# Set up environment variables
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
export JIRA_URL=https://jira.example.com
export JIRA_TOKEN=xxxxxxxxxxxxxxxx

# Build and start the container
docker-compose build
docker-compose run shift-left-tooling bash
```

### Option 2: Local Python Environment

```bash
# Clone the repository
git clone https://github.com/troyfontaine/shift-left-tooling.git
cd shift-left-tooling

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
export JIRA_URL=https://jira.example.com
export JIRA_TOKEN=xxxxxxxxxxxxxxxx

# Run scripts directly
python scripts/get_protected_branches.py
```

## Running Tests

Pytest tests are configured via pyproject.toml to always check `lib/` and `scripts/`

```bash
# With Docker Compose
docker-compose run shift-left-tooling pytest tests/

# Locally
pytest tests/ --cov-report=html --cache-clear

# With verbose output
pytest tests/ -v --cache-clear
```

## Code Quality

### Black (Code Formatting)

```bash
# Check formatting
docker-compose run shift-left-tooling black --check lib/ scripts/

# Auto-format
docker-compose run shift-left-tooling black lib/ scripts/
```

### Pylint (Linting)

```bash
# Run linter
docker-compose run shift-left-tooling pylint lib/ scripts/

# Run on specific file
docker-compose run shift-left-tooling pylint scripts/get_protected_branches.py
```

### MyPy (Type Checking)

```bash
# Check types
docker-compose run shift-left-tooling mypy lib/ scripts/

# Verbose output
docker-compose run shift-left-tooling mypy lib/ scripts/ --verbose
```

### All Checks Together

```bash
docker-compose run shift-left-tooling sh -c "\
  black --check lib/ scripts/ && \
  pylint lib/ scripts/ && \
  mypy lib/ scripts/ && \
  pytest tests/ --cov=lib --cov=scripts --cov-fail-under=80"
```

## Building Docker Image

### Local Build

```bash
# Build image locally
docker build -t shift-left-tooling:dev .

# Run image
docker run -e GITHUB_TOKEN=ghp_xxxx shift-left-tooling:dev get-protected-branches
```

### Multi-Stage Build

The Dockerfile uses multi-stage build to reduce image size:

```bash
# Build only base stage
docker build --target base -t shift-left-tooling:base .
```

## Project Structure

```
shift-left-tooling/
├── scripts/                      # CLI entry points
│   ├── __init__.py
│   ├── get_protected_branches.py
│   ├── validate_branch_name.py
│   ├── enforce_protected_branches.py
│   ├── validate_branch_naming.py
│   ├── validate_jira_commit_link.py
│   └── generate_changelog.py
├── lib/                          # Shared libraries
│   ├── __init__.py
│   ├── config.py                 # Configuration & env vars
│   ├── git_utils.py              # Git operations
│   ├── github_provider.py        # GitHub API client
│   └── jira_provider.py          # Jira API client
├── tests/                        # Unit tests
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_git_utils.py
│   ├── test_github_provider.py
│   └── test_scripts.py
├── docs/                         # Documentation
│   └── DEVELOPMENT.md            # This file
├── .github/workflows/            # GitHub Actions
├── .lefthook/                    # Lefthook hook scripts
├── Dockerfile                    # Docker image definition
├── docker-compose.yml            # Local dev compose
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Tool configuration
├── pytest.ini                    # Pytest configuration
├── .flake8                       # Flake8 configuration
├── docker-entrypoint.sh         # Container entrypoint
├── docker-entrypoint.sh         # Container entrypoint
├── .dockerignore                 # Docker build ignore
├── README.md                     # Project README
└── lefthook.yml                  # Lefthook config
```

## Adding New Features

### Adding a New Script

1. Create `scripts/new_script_name.py` with:
   - Shebang line: `#!/usr/bin/env python3`
   - Docstring with usage and options
   - `main()` function returning exit code
   - Proper logging and error handling

2. Example structure:
   ```python
   #!/usr/bin/env python3
   """Description of script."""

   import argparse
   import logging
   import sys

   logger = logging.getLogger(__name__)

   def main() -> int:
       """Main entry point."""
       parser = argparse.ArgumentParser(description="...")
       args = parser.parse_args()

       try:
           # Implementation
           return 0
       except Exception as e:
           logger.error(f"Error: {e}")
           return 1

   if __name__ == "__main__":
       sys.exit(main())
   ```

3. Update `docker-entrypoint.sh` to handle new script name
4. Add tests in `tests/test_scripts.py`
5. Update Dockerfile CMD
6. Document in README.md

### Adding a Library Module

1. Create `lib/new_module.py` with proper docstrings
2. Add type hints throughout
3. Create tests in `tests/test_new_module.py`
4. Use mocking for external API calls
5. Ensure 100% type coverage with mypy

## Debugging

### Enable Debug Logging

```bash
export LOG_LEVEL=debug
docker-compose run shift-left-tooling get-protected-branches
```

### Interactive Shell

```bash
# SSH into container
docker-compose run shift-left-tooling bash

# Run Python interpreter
docker-compose run shift-left-tooling python
```

### Mount Local Code

For testing local changes without rebuilding:

```bash
docker-compose run \
  -v $(pwd)/lib:/app/lib:ro \
  -v $(pwd)/scripts:/app/scripts:ro \
  shift-left-tooling get-protected-branches
```

## GitHub Actions Workflows

Workflows are defined in `.github/workflows/`:

- `pr-tests.yml` - Runs on pull requests (lint, type check, tests)
- `build-and-publish.yml` - Builds and publishes to Docker Hub on main/release

### Local Testing of Workflows

```bash
# Install act
brew install act

# Run workflow locally
act pull_request
act push
```

## Credentials & Secrets

### Local Development

Create `.env` file (not committed):

```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
JIRA_URL=https://jira.example.com
JIRA_TOKEN=xxxxxxxxxxxxxxxx
BRANCH_NAMING_PATTERN=^[A-Z]+-\d+
LOG_LEVEL=debug
```

### GitHub Actions Secrets

Set in repository settings > Secrets and variables:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `GITHUB_TOKEN`

## Performance Profiling

```bash
# Profile a script
docker-compose run shift-left-tooling \
  python -m cProfile -s cumulative scripts/get_protected_branches.py

# Measure execution time
time python scripts/get_protected_branches.py
```

## Common Issues

### GitHub Token Expired

```bash
# Generate new token at github.com/settings/tokens
export GITHUB_TOKEN=ghp_newtoken
```

### Jira Authentication Failed

- Verify URL format: `https://jira.example.com` (with https://)
- Verify token is not expired
- Try with username: `automation`

### Tests Failing with Mock Issues

- Ensure mocks match actual API signatures
- Check patch paths are correct (e.g., `lib.github_provider.Github`)
- Verify mock return values are set

## Continuous Integration

### Pre-Push Checks

```bash
# Run all checks before pushing
docker-compose run shift-left-tooling sh -c "\
  black --check lib/ scripts/ && \
  pylint lib/ scripts/ && \
  mypy lib/ scripts/ && \
  pytest tests/ --cov=lib --cov=scripts --cov-fail-under=80"
```

### Git Hooks

Install Lefthook for automatic checks:

```bash
brew install lefthook
lefthook install

# Hooks will run on:
# - git commit (linting, type checking)
# - git push (protected branch check)
# - git commit-msg (Jira validation)
```

## Code Style Guidelines

- **Line Length**: 100 characters max
- **Imports**: Use absolute imports from project root
- **Type Hints**: All functions should have type hints
- **Docstrings**: All modules, classes, functions
- **Comments**: Use when logic is not obvious
- **Logging**: Use structured logging with logger.info(), logger.error()

## Release Process

1. Update version in code and docs
2. Create CHANGELOG entry
3. Tag release: `git tag v1.0.0`
4. Push to main: `git push --tags`
5. GitHub Action builds and publishes to Docker Hub

## Support & Questions

- 📖 Check [README.md](../README.md)
- 🐛 Open an [Issue](https://github.com/troyfontaine/shift-left-tooling/issues)
- 💬 Start a [Discussion](https://github.com/troyfontaine/shift-left-tooling/discussions)
