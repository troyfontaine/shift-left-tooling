# Contributing to Shift-Left Tooling

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the shift-left-tooling project.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/shift-left-tooling.git`
3. Add upstream: `git remote add upstream https://github.com/troyfontaine/shift-left-tooling.git`
4. Create a feature branch: `git checkout -b feature/PROJ-123-feature-name`

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed setup instructions.

## Making Changes

### Branch Naming

Follow Jira ticket naming convention:

- `feature/PROJ-123-description` - New features
- `bugfix/PROJ-123-description` - Bug fixes
- `refactor/PROJ-123-description` - Code refactoring
- `docs/PROJ-123-description` - Documentation updates

### Commit Messages

Include Jira ticket reference:

```text
PROJ-123: Brief description of change

More detailed explanation if needed. This helps with changelog generation.
```

### Code Style

- **Python**: Follow PEP-8 via Black (80 char line length)
- **Type Hints**: All functions must have type hints
- **Docstrings**: All modules, classes, and functions must have docstrings
- **Tests**: Add tests for all new functionality

Run code quality checks:

```bash
docker-compose run shift-left-tooling sh -c "\
  black lib/ scripts/ && \
  pylint lib/ scripts/ && \
  mypy lib/ scripts/"
```

### Testing

Add tests for any new code. Minimum coverage required: **80%**

```bash
# Run tests
docker-compose run shift-left-tooling pytest tests/ --cov=lib --cov=scripts

# With coverage report
docker-compose run shift-left-tooling pytest tests/ \
  --cov=lib \
  --cov=scripts \
  --cov-report=html
```

## Submitting Changes

### Pull Request Process

1. Update [README.md](README.md) with any new features or changes
2. Update [CHANGELOG.md](CHANGELOG.md) under `[Unreleased]`
3. Ensure all tests pass and coverage is ≥80%
4. Push to your fork: `git push origin feature/PROJ-123-feature-name`
5. Create a pull request with a clear description
6. Link the issue/ticket in the PR description

### PR Template

```markdown
## Description
Brief description of changes

## Related Issues
Fixes #123 or Relates to PROJ-123

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## How Has This Been Tested?
Describe how you tested the changes.

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] All tests pass
- [ ] Coverage maintained at ≥80%
```

## Review Process

1. Automated checks run (linting, tests, type checking)
2. Code review by maintainers
3. Approval and merge to main (requires passing checks)
4. Docker image automatically published to Docker Hub

## Development Tips

### Running Individual Scripts

```bash
# With local Python
python scripts/get_protected_branches.py

# With Docker Compose
docker-compose run shift-left-tooling get-protected-branches
```

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=debug
docker-compose run shift-left-tooling get-protected-branches

# Interactive debugging
docker-compose run shift-left-tooling python -pdb scripts/script_name.py
```

### Adding New Features

1. Create new script in `scripts/` or module in `lib/`
2. Add comprehensive tests in `tests/`
3. Update `docker-entrypoint.sh` for new scripts
4. Document in README.md
5. Add CHANGELOG entry

## Documentation

- **README.md** - User-facing documentation
- **docs/DEVELOPMENT.md** - Developer documentation
- **Inline comments** - Explain non-obvious logic
- **Docstrings** - All public APIs

## Reporting Issues

Use GitHub Issues for:

- Bug reports
- Feature requests
- Documentation improvements

Provide:

- Clear description of the issue
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)

## Questions?

- 📖 Check [README.md](README.md) and [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- 💬 Create a GitHub Discussion
- 🐛 Open an Issue

## Recognition

Contributors will be recognized in:

- CHANGELOG.md
- Release notes
- GitHub contributors page

Thank you for contributing! 🎉
