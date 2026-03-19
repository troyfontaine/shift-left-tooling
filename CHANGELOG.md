# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of shift-left-tooling
- Docker-based CLI tools for Git and Jira integration
- Protected branch enforcement script
- Branch naming validation with configurable patterns
- Jira ticket link validation in commit messages
- GitHub protected branch querying
- Changelog generation from commit history
- Lefthook integration for pre-commit, pre-push, and commit-msg hooks
- Comprehensive test suite with >80% coverage
- GitHub Actions workflows for CI/CD
- Docker Hub publishing on main branch and releases
- Development documentation and setup guides

### Features
- 🔒 Protected Branch Enforcement
- 📝 Branch Naming Validation
- 🎫 Jira Integration
- 🐙 GitHub Integration
- 📋 Changelog Generation
- 🪝 Lefthook Integration
- 🐳 Docker-Ready
- ✅ CLI & Hook Modes

### Supported Platforms
- **GitHub** - ✅ Full support for protected branches and issue validation
- **Jira** - ✅ Full support for ticket validation and changelog generation
- **GitLab** - ❌ Stubbed (planned for future release)
- **Bitbucket** - ❌ Stubbed (planned for future release)

## [0.1.0] - 2026-03-18

### Added
- Initial implementation of core scripts:
  - `get-protected-branches` - Query protected branches from GitHub
  - `validate-branch-name` - Validate branch names against Jira/GitHub patterns
  - `enforce-protected-branches` - Prevent pushes to protected branches
  - `validate-branch-naming` - Validate naming conventions
  - `validate-jira-commit-link` - Ensure commits reference Jira tickets
  - `generate-changelog` - Generate changelogs from commits

### Added
- Shared libraries:
  - `git_utils.py` - Git operations and provider detection
  - `github_provider.py` - GitHub API wrapper using PyGithub
  - `jira_provider.py` - Jira API wrapper with stubs for other providers
  - `config.py` - Environment variable management with Pydantic

### Added
- Project infrastructure:
  - Dockerfile for Python 3.12 environment
  - Docker Compose for local development
  - Comprehensive test suite with pytest
  - Code quality tools: Black, Pylint, MyPy
  - Lefthook configuration with pre-commit/pre-push/commit-msg hooks
  - GitHub Actions workflows for CI/CD

### Added
- Documentation:
  - Comprehensive README with usage examples
  - Development guide with setup instructions
  - Inline code documentation with docstrings
  - Environment variable reference
  - Supported providers matrix

---

## Future Roadmap

### Planned Features
- [ ] GitLab support for protected branches and issue validation
- [ ] Bitbucket support for branch/issue operations
- [ ] Advanced changelog features (custom templates, grouping by label)
- [ ] Slack integration for notifications
- [ ] Performance metrics and analytics
- [ ] Web dashboard for branch management
- [ ] Support for custom validation rules
- [ ] Multi-repository analysis

### Performance Improvements
- [ ] Cache GitHub/Jira API responses
- [ ] Parallel processing of multiple repositories
- [ ] Optimize Docker image size (<200MB)

### Documentation
- [ ] Video tutorials
- [ ] Advanced configuration guide
- [ ] Integration examples
- [ ] Contribution guidelines

---

[Unreleased]: https://github.com/troyfontaine/shift-left-tooling/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/troyfontaine/shift-left-tooling/releases/tag/v0.1.0
