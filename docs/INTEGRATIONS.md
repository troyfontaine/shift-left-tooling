# External Tool Integrations

This document describes how to integrate language-specific linting and static analysis tools alongside shift-left-tooling using Lefthook. These tools are **not bundled** in the shift-left-tooling image to keep it lean and focused on Git/Jira workflow enforcement. Instead, they are invoked via their own official container images.

## Philosophy

| shift-left-tooling (this image) | External containers               |
|---                              | ---                               |
| Branch naming validation        | Terraform linting (tflint)        |
| Jira ticket linking             | Ansible linting (ansible-lint)    |
| Protected branch enforcement    | IaC policy checking (checkov)     |
| YAML/JSON well-formedness       | Language-specific static analysis |
| Changelog generation            |                                   |

Each external tool is invoked directly via `docker run` in a lefthook hook, so no global installation is required on developer machines beyond Docker and Lefthook itself.

---

## Terraform

### Tool: tflint

[tflint](https://github.com/terraform-linters/tflint) lints `.tf` files for errors, deprecated syntax, and provider-specific best practices.

**Prerequisite:** A `.tflint.hcl` config file in the repository root. At minimum:

```hcl
# .tflint.hcl
config {
  format = "default"
}
```

**lefthook.yml snippet:**

```yaml
pre-commit:
  jobs:
    - name: tflint
      glob: "*.tf"
      run: |
        for dir in $(printf '%s\n' {staged_files} | xargs -I{} dirname {} | sort -u); do
          docker run --rm \
            -v "$(git rev-parse --show-toplevel):/data" \
            -w /data \
            ghcr.io/terraform-linters/tflint:latest \
            --chdir="$dir"
        done
```

> **Note:** tflint evaluates a module directory, not individual files. The loop above extracts all unique directories from the staged `.tf` files and runs tflint once per directory, correctly handling monorepos with multiple Terraform modules.

---

## Terragrunt

Terragrunt is a thin wrapper around Terraform, so underlying `.tf` files are still linted by tflint using the same snippet above. For live infrastructure directories containing `terragrunt.hcl` files, add a Checkov step for IaC policy enforcement:

### Tool: Checkov (IaC policy)

[Checkov](https://github.com/bridgecrewio/checkov) performs static analysis of Terraform, Terragrunt, and other IaC formats against security and compliance policies.

**lefthook.yml snippet:**

```yaml
pre-commit:
  jobs:
    - name: checkov
      glob: "*.tf,*.hcl"
      run: |
        docker run --rm \
          -v "$(git rev-parse --show-toplevel):/data" \
          -w /data \
          bridgecrew/checkov:latest \
          --directory . \
          --quiet
```

> **Note:** Checkov supports a `.checkov.yaml` config file in the repo root for customizing checks, skipping rules, and setting output format.

---

## Ansible

### Tool: ansible-lint

[ansible-lint](https://github.com/ansible/ansible-lint) enforces best practices for Ansible playbooks, roles, and task files.

**Prerequisite:** An `.ansible-lint` config file in the repository root. At minimum:

```yaml
# .ansible-lint
profile: moderate
exclude_paths:
  - .cache/
  - .venv/
```

**lefthook.yml snippet:**

```yaml
pre-commit:
  jobs:
    - name: ansible-lint
      glob: "playbooks/*.yml,roles/**/*.yml,tasks/*.yml"
      run: |
        docker run --rm \
          -v "$(git rev-parse --show-toplevel):/data" \
          -w /data \
          ghcr.io/ansible/ansible-lint:latest \
          {staged_files}
```

> **Note:** ansible-lint distinguishes Ansible YAML from generic YAML by convention and config. Scoping the glob to `playbooks/`, `roles/`, and `tasks/` directories prevents it from running on non-Ansible YAML files (e.g., CI configs, Docker Compose files).

---

## Combined Example

A complete `lefthook.yml` pre-commit block combining shift-left-tooling's built-in hooks with all of the external tool hooks above:

```yaml
pre-commit:
  parallel: true
  jobs:
    # --- shift-left-tooling built-in hooks ---
    - name: pylint
      glob: "*.py"
      run: pylint {staged_files} --fail-under=8.0

    - name: black-check
      glob: "*.py"
      run: black --check {staged_files}

    - name: mypy
      glob: "*.py"
      run: mypy {staged_files}

    - name: enforce-naming
      runner: bash
      run: ./.lefthook/pre-commit/enforce-naming

    - name: yamllint
      glob: "*.yml,*.yaml"
      run: python3 scripts/validate_yaml.py {staged_files}

    - name: jsonlint
      glob: "*.json"
      run: python3 scripts/validate_json.py {staged_files}

    # --- External tool hooks (Docker-based) ---
    - name: tflint
      glob: "*.tf"
      run: |
        for dir in $(printf '%s\n' {staged_files} | xargs -I{} dirname {} | sort -u); do
          docker run --rm \
            -v "$(git rev-parse --show-toplevel):/data" \
            -w /data \
            ghcr.io/terraform-linters/tflint:latest \
            --chdir="$dir"
        done

    - name: checkov
      glob: "*.tf,*.hcl"
      run: |
        docker run --rm \
          -v "$(git rev-parse --show-toplevel):/data" \
          -w /data \
          bridgecrew/checkov:latest \
          --directory . \
          --quiet

    - name: ansible-lint
      glob: "playbooks/*.yml,roles/**/*.yml,tasks/*.yml"
      run: |
        docker run --rm \
          -v "$(git rev-parse --show-toplevel):/data" \
          -w /data \
          ghcr.io/ansible/ansible-lint:latest \
          {staged_files}
```

> **Tip:** Use a `.lefthook.local.yml` in each developer's local clone to disable specific hooks that don't apply to their work (e.g., a developer not working on Terraform can disable tflint locally without affecting CI).
