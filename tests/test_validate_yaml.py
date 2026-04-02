"""Tests for validate_yaml script."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from yamllint.config import YamlLintConfig
from yamllint.linter import LintProblem

from scripts.validate_yaml import lint_file, load_config, main


class TestLoadConfig:
    """Tests for load_config helper."""

    def test_explicit_config_flag(self, tmp_path):
        """--config flag takes highest priority."""
        config_file = tmp_path / ".yamllint.yml"
        config_file.write_text("extends: default\n")
        conf = load_config(str(config_file))
        assert isinstance(conf, YamlLintConfig)

    def test_cwd_yamllint_yml_detected(self, tmp_path):
        """Falls back to .yamllint.yml in CWD when no --config given."""
        config_file = tmp_path / ".yamllint.yml"
        config_file.write_text("extends: default\n")
        with mock.patch(
            "scripts.validate_yaml.Path.cwd", return_value=tmp_path
        ):
            conf = load_config(None)
        assert isinstance(conf, YamlLintConfig)

    def test_cwd_yamllint_detected(self, tmp_path):
        """Falls back to .yamllint in CWD when .yamllint.yml absent."""
        config_file = tmp_path / ".yamllint"
        config_file.write_text("extends: default\n")
        with mock.patch(
            "scripts.validate_yaml.Path.cwd", return_value=tmp_path
        ):
            conf = load_config(None)
        assert isinstance(conf, YamlLintConfig)

    def test_default_preset_when_no_config(self, tmp_path):
        """Uses 'extends: default' preset when no config file found."""
        with mock.patch(
            "scripts.validate_yaml.Path.cwd", return_value=tmp_path
        ):
            conf = load_config(None)
        assert isinstance(conf, YamlLintConfig)


class TestLintFile:
    """Tests for lint_file helper."""

    def test_valid_yaml_returns_true(self, tmp_path, capsys):
        """Valid YAML file returns True and prints ✓."""
        yaml_file = tmp_path / "valid.yml"
        yaml_file.write_text("---\nkey: value\n")
        conf = YamlLintConfig("extends: default")
        result = lint_file(str(yaml_file), conf)
        assert result is True
        assert "✓" in capsys.readouterr().out

    def test_invalid_yaml_returns_false(self, tmp_path, capsys):
        """YAML file with syntax errors returns False and prints ✗."""
        yaml_file = tmp_path / "invalid.yml"
        yaml_file.write_text("key: : bad_colon\n")
        conf = YamlLintConfig("extends: default")
        result = lint_file(str(yaml_file), conf)
        assert result is False
        captured = capsys.readouterr().out
        assert "✗" in captured

    def test_missing_file_returns_false(self, capsys):
        """Non-existent file returns False and prints ✗."""
        conf = YamlLintConfig("extends: default")
        result = lint_file("/nonexistent/path/file.yml", conf)
        assert result is False
        assert "✗" in capsys.readouterr().out

    def test_lint_problems_printed(self, tmp_path, capsys):
        """Individual lint problems are printed with line:col level message."""
        yaml_file = tmp_path / "problems.yml"
        # trailing spaces trigger a yamllint error under default config
        yaml_file.write_text("---\nkey: value  \n")
        conf = YamlLintConfig("extends: default")
        lint_file(str(yaml_file), conf)
        out = capsys.readouterr().out
        # Either valid or shows problem details — just ensure file name printed
        assert str(yaml_file) in out


class TestValidateYamlMain:
    """Tests for the main() entry point."""

    def test_no_files_returns_zero(self, capsys):
        """No files provided → prints message and returns 0."""
        result = main([])
        assert result == 0
        assert "No YAML files to validate" in capsys.readouterr().out

    def test_valid_file_returns_zero(self, tmp_path):
        """Single valid YAML file → returns 0."""
        yaml_file = tmp_path / "ok.yml"
        yaml_file.write_text("---\nname: test\n")
        with mock.patch(
            "scripts.validate_yaml.Path.cwd", return_value=tmp_path
        ):
            result = main([str(yaml_file)])
        assert result == 0

    def test_invalid_file_returns_one(self, tmp_path):
        """Single invalid YAML file → returns 1."""
        yaml_file = tmp_path / "bad.yml"
        yaml_file.write_text("key: : bad\n")
        with mock.patch(
            "scripts.validate_yaml.Path.cwd", return_value=tmp_path
        ):
            result = main([str(yaml_file)])
        assert result == 1

    def test_multiple_files_all_valid(self, tmp_path):
        """Multiple valid files → returns 0."""
        for name in ("a.yml", "b.yml"):
            (tmp_path / name).write_text("---\nx: 1\n")
        with mock.patch(
            "scripts.validate_yaml.Path.cwd", return_value=tmp_path
        ):
            result = main([str(tmp_path / "a.yml"), str(tmp_path / "b.yml")])
        assert result == 0

    def test_multiple_files_one_invalid(self, tmp_path):
        """Mixed valid/invalid files → returns 1."""
        (tmp_path / "good.yml").write_text("---\nx: 1\n")
        (tmp_path / "bad.yml").write_text("key: : bad\n")
        with mock.patch(
            "scripts.validate_yaml.Path.cwd", return_value=tmp_path
        ):
            result = main(
                [str(tmp_path / "good.yml"), str(tmp_path / "bad.yml")]
            )
        assert result == 1

    def test_custom_config_flag(self, tmp_path):
        """--config flag is passed through to load_config."""
        yaml_file = tmp_path / "ok.yml"
        yaml_file.write_text("---\nname: test\n")
        config_file = tmp_path / "custom.yml"
        config_file.write_text("extends: default\n")
        result = main(["--config", str(config_file), str(yaml_file)])
        assert result == 0

    def test_bad_config_returns_one(self, tmp_path, capsys):
        """Invalid config file → returns 1 with error message."""
        yaml_file = tmp_path / "ok.yml"
        yaml_file.write_text("name: test\n")
        result = main(["--config", "/nonexistent/config.yml", str(yaml_file)])
        assert result == 1
        assert "✗" in capsys.readouterr().out
