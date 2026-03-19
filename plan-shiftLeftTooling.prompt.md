# Plan: Docker Container for Shift-Left Git & Jira Tooling

## TL;DR
Build a Python 3.12 Docker container with 6 specialized scripts for pre-commit validation: querying protected branches from GitHub, validating branch names against Jira/GitHub, enforcing protected branch restrictions, validating branch naming conventions, validating Jira links in commits, and generating changelogs. Scripts integrate with Lefthook for automatic hook execution and can be called as standalone CLI tools. Publish to Docker Hub with GitHub Actions CI/CD. Requires GITHUB_TOKEN environment variable for API access.

---

## Steps

### Phase 1: Project Structure & Docker Setup (foundational)
1. Create `Dockerfile` (Python 3.12 base) with dependencies for GitHub SDK (`PyGithub`), Jira SDK (`jira-python`), and linting tools (pylint, black, mypy)
2. Create `requirements.txt` with pinned versions for GitHub SDK, Jira SDK, pydantic (validation), and dev dependencies (pytest, pytest-cov, black, pylint, mypy)
3. Create `docker-compose.yml` for local development mounting `.git` directory and environment variables
4. Create `scripts/` directory structure:
   - `scripts/get_protected_branches.py` — Query GitHub protected branches
   - `scripts/validate_branch_name.py` — Check Jira/GitHub ticket validity
   - `scripts/enforce_protected_branches.py` — Block pushes to protected branches
   - `scripts/validate_branch_naming.py` — Check naming conventions
   - `scripts/validate_jira_commit_link.py` — Ensure commits reference Jira tickets
   - `scripts/generate_changelog.py` — Build changelog from commits/tickets
5. Create `lib/` directory for shared utilities:
   - `lib/git_utils.py` — Git repo detection, origin extraction, current branch
   - `lib/github_provider.py` — GitHub API client wrapper
   - `lib/jira_provider.py` — Jira API client wrapper (stub BitBucket, GitLab)
   - `lib/config.py` — Environment variable loading & validation

### Phase 2: Core Script Implementation (depends on Phase 1)
1. **get_protected_branches.py** — GitHub only (primary)
   - Mount `.git` directory, extract origin URL
   - Detect provider (GitHub primary)
   - Query GitHub API via PyGithub for protected branches
   - Return JSON list of branch names
   - Stub BitBucket & GitLab with "not implemented" messages

2. **validate_branch_name.py**
   - Accept branch name argument & API credentials
   - Check if it matches Jira ticket pattern (e.g., `PROJ-123`) or GitHub issue pattern (`#1234`)
   - Query Jira/GitHub to verify ticket/issue exists
   - Return exit code 0 (valid) or 1 (invalid)

3. **enforce_protected_branches.py**
   - Get current branch, check against protected list
   - Block pushes to protected branches
   - Return clear error message if protected

4. **validate_branch_naming.py**
   - Define naming convention (configurable regex, default: `[A-Z]+-\d+.*` for Jira)
   - Accept branch name, validate against pattern
   - Return exit code 0 (valid) or 1 (invalid)

5. **validate_jira_commit_link.py**
   - Extract commit message
   - Validate presence of Jira ticket reference
   - Optionally query Jira to verify ticket exists
   - Return exit code 0 (valid) or 1 (invalid)

6. **generate_changelog.py**
   - Scan commits in range (e.g., last 10 commits or since last tag)
   - Extract Jira tickets, group by ticket
   - Generate markdown or plaintext changelog
   - Write to file or stdout

### Phase 3: Shared Libraries Implementation (depends on Phase 1)
1. **git_utils.py** — Utilities for:
   - Reading `.git/config` for origin detection
   - Extracting GitHub org/repo from URL
   - Getting current branch
   - Parsing commit messages

2. **github_provider.py**
   - PyGithub wrapper with GITHUB_TOKEN loading
   - Methods: `get_protected_branches()`, `get_issue()`, `validate_issue_exists()`
   - Error handling for missing token or API failures

3. **jira_provider.py**
   - Jira SDK wrapper with JIRA_URL and JIRA_TOKEN loading
   - Methods: `get_ticket()`, `validate_ticket_exists()`
   - Stub implementations for BitBucket, GitLab (return "not implemented")

4. **config.py**
   - Load environment variables: `GITHUB_TOKEN`, `JIRA_URL`, `JIRA_TOKEN`, `BRANCH_NAMING_PATTERN`
   - Validate required vars present
   - Provide defaults where appropriate

### Phase 4: Testing & Linting (depends on Phases 2-3)
1. Create `tests/` directory with unit tests for each script
   - Mock GitHub/Jira API calls
   - Test valid/invalid branch names
   - Test with and without credentials
2. Add pytest configuration (`pytest.ini`)
3. Create `.flake8` and `pyproject.toml` for black/pylint config
4. Test scripts locally with docker-compose

### Phase 5: Lefthook Integration (depends on Phase 2)
1. Update `lefthook.yml` to add new hooks:
   - pre-push: `enforce_protected_branches.py`
   - pre-commit: `validate_branch_naming.py`, `validate_jira_commit_link.py`
   - Add linting & syntax checks for Python scripts (pylint, black --check, mypy)
2. Create hook scripts in `.lefthook/pre-commit/` and `.lefthook/pre-push/` that invoke Docker container
3. Update `.lefthook/commit-msg/` hook to support Jira link validation

### Phase 6: Documentation & README (depends on Phases 2-5)
1. Update `README.md` with:
   - High-level overview of each script
   - Required environment variables table (GITHUB_TOKEN, JIRA_URL, JIRA_TOKEN, BRANCH_NAMING_PATTERN)
   - Installation instructions (Docker / local Python)
   - Usage examples for each script (CLI & Lefthook integration)
   - Configuration/customization guide
   - Supported providers matrix (GitHub ✓, Jira ✓, BitBucket ✗, GitLab ✗)
2. Create `docs/DEVELOPMENT.md` with local setup instructions
3. Add inline comments to scripts for maintainability

### Phase 7: CI/CD & Publishing (depends on Phase 4)
1. Create `.github/workflows/build-and-publish.yml`
   - Trigger on: push to main, manual dispatch, release tags
   - Run tests & linting in Docker
   - Build image with semantic versioning tags
   - Push to Docker Hub (requires DOCKERHUB_USERNAME & DOCKERHUB_TOKEN secrets)
2. Update `.github/workflows/` for PR testing (lint & unit tests only, no publish)
3. Add CODEOWNERS file referencing maintainers

### Phase 8: Dockerfile & Kubernetes-Ready Extras (depends on Phase 3)
1. Finalize `Dockerfile`:
   - Multi-stage build if needed (reduce final image size)
   - Install dependencies from requirements.txt
   - Copy scripts & lib directories
   - Set entrypoint or CMD to support both CLI & container modes
   - Add healthcheck if running as service
2. Create `docker-entrypoint.sh` to handle script routing (which script to run based on arguments)
3. Create `.dockerignore` to exclude test files, .git, etc.

---

## Relevant Files
- `Dockerfile` — Docker image definition (Python 3.12, dependencies)
- `requirements.txt` — Python dependencies (PyGithub, jira, pydantic, pytest, black, pylint, mypy)
- `docker-compose.yml` — Local development setup (mount .git, set env vars)
- `scripts/*.py` — 6 Python scripts for branch/commit validation
- `lib/*.py` — Shared libraries (git_utils, github_provider, jira_provider, config)
- `README.md` — Updated documentation (env vars, usage, supported providers)
- `docs/DEVELOPMENT.md` — Local development guide
- `lefthook.yml` — Updated hook configuration
- `.lefthook/pre-commit/*` — Hook scripts for linting & syntax checks
- `.lefthook/pre-push/*` — Hook scripts for protected branch enforcement
- `.lefthook/commit-msg/*` — Hook scripts for Jira link validation
- `.github/workflows/build-and-publish.yml` — Push to Docker Hub on main/release
- `.github/workflows/pr-tests.yml` — Run tests & linting on PRs
- `tests/*.py` — Unit tests with mocked API calls
- `pyproject.toml` — Black, pylint, mypy configuration
- `.dockerignore` — Exclude non-essential files from image

---

## Verification

1. **Unit Tests** — Run `pytest tests/` inside container; verify ≥90% code coverage
2. **Linting** — Run `pylint scripts/ lib/` & `black --check scripts/ lib/`; ensure no errors
3. **Type Checking** — Run `mypy scripts/ lib/`; ensure all type hints pass
4. **Docker Build** — Build image locally; verify no errors: `docker build -t shift-left-tooling .`
5. **Local Integration**
   - Run `docker-compose up` and test each script manually
   - Verify Lefthook hooks trigger correctly in a test Git repo
6. **CLI Invocation** — Test both Docker and native Python invocation for each script
7. **GitHub Actions** — Verify workflows build, test, and publish to Docker Hub on main branch
8. **Documentation Review** — Verify README env var table matches actual implementation
9. **Provider Stub Testing** — Confirm BitBucket/GitLab gracefully return "not implemented" messages

---

## Decisions

- **GitHub Primary, Jira Primary** — GitHub for protected branches (primary), Jira for ticket validation (primary); BitBucket & GitLab stubbed with clear error messages
- **Token-Based Auth** — GITHUB_TOKEN via environment variable (no SSH key mounting) for simplicity
- **Python 3.12** — Latest stable for better performance & type hints
- **Docker Hub Distribution** — Public accessibility; easier for external teams
- **Dual-Mode Execution** — Scripts callable both via Lefthook hooks AND as standalone CLI
- **PyGithub & Jira SDK** — Official vendor SDKs prioritized over custom HTTP clients
- **Lefthook Integration** — New hooks for pre-push & commit-msg; reuse existing pre-commit structure

---

## Further Considerations

1. **Scope of Changelog Generation**
   - What commit range should be scanned? (Last N commits / since last tag / between two tags)
   - Recommendation: Support all three via CLI flags (--last-n-commits, --since-tag, --tag-range)

2. **Branch Naming Convention Flexibility**
   - Should naming pattern be configurable per repo (via env var) or hardcoded?
   - Recommendation: Configurable via `BRANCH_NAMING_PATTERN` env var with sensible defaults

3. **Credential Handling in Lefthook**
   - Should env vars be set in developer's shell, `.env` file, or .lefthook config?
   - Recommendation: Support all three (env var → .env file fallback → defaults)
