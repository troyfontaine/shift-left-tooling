#!/bin/bash
# Pre-commit hook for validating branch naming conventions
# This script validates the current branch name follows the configured pattern

set -e

# Source the Docker-based validation script
docker-compose run --rm shift-left-tooling validate-branch-naming

exit $?
