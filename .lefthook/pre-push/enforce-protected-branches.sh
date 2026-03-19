#!/bin/bash
# Pre-push hook for enforcing protected branch restrictions
# This script prevents pushes to protected branches

set -e

# Source the Docker-based protection script
docker-compose run --rm shift-left-tooling enforce-protected-branches

exit $?
