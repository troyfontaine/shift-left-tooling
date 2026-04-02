#!/bin/bash
# Docker entrypoint for shift-left-tooling
# Routes commands to the appropriate Python script

set -euo pipefail

SCRIPT_DIR="/app/scripts"
COMMAND="${1:-}"

# Display help if no command provided
if [[ -z "$COMMAND" ]] || [[ "$COMMAND" == "--help" ]] || [[ "$COMMAND" == "-h" ]]; then
  cat << 'EOF'
Shift-Left Tooling - Docker Container

Available commands:
  get-protected-branches         Query GitHub for protected branches in current repo
  validate-branch-name           Validate branch name against Jira/GitHub ticket patterns
  enforce-protected-branches     Prevent pushes to protected branches (pre-push hook)
  validate-branch-naming         Validate branch follows naming convention
  validate-jira-commit-link      Ensure commit messages reference valid Jira tickets
  generate-changelog             Generate changelog from commit history
  validate-yaml                  Validate YAML files for syntax and style
  validate-json                  Validate JSON files for well-formedness

Usage:
  docker run <image> <command> [options]

Examples:
  docker run shift-left-tooling get-protected-branches
  docker run shift-left-tooling validate-branch-name PROJ-123
  docker run shift-left-tooling validate-branch-naming my-feature-branch

Environment Variables:
  GITHUB_TOKEN                   GitHub API token (required for GitHub operations)
  JIRA_URL                       Jira instance URL (required for Jira operations)
  JIRA_TOKEN                     Jira API token (required for Jira operations)
  BRANCH_NAMING_PATTERN          Regex pattern for branch naming validation
  LOG_LEVEL                      Logging level (debug, info, warning, error)

For script-specific help:
  docker run shift-left-tooling <command> --help
EOF
  exit 0
fi

# Remove leading dashes if present (handles 'get-protected-branches' or 'get_protected_branches')
COMMAND_NORMALIZED=$(echo "$COMMAND" | tr '-' '_')
SCRIPT_PATH="${SCRIPT_DIR}/${COMMAND_NORMALIZED}.py"

# Check if script exists
if [[ ! -f "$SCRIPT_PATH" ]]; then
  echo "Error: Unknown command '$COMMAND'" >&2
  echo "Run 'docker run <image>' for available commands" >&2
  exit 1
fi

# Execute the script with remaining arguments
shift 1
exec env PYTHONPATH=/app:${PYTHONPATH:-} python3 "$SCRIPT_PATH" "$@"
