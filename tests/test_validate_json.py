"""Tests for validate_json script."""

import json
import tempfile
from pathlib import Path

from scripts.validate_json import main, validate_file


class TestValidateFile:
    """Tests for the validate_file helper."""

    def test_valid_json_object_returns_true(self, tmp_path, capsys):
        """Valid JSON object returns True and prints ✓."""
        f = tmp_path / "valid.json"
        f.write_text('{"key": "value"}')
        assert validate_file(str(f)) is True
        assert "✓" in capsys.readouterr().out

    def test_valid_empty_object_returns_true(self, tmp_path):
        """Empty JSON object {} is valid and returns True."""
        f = tmp_path / "empty.json"
        f.write_text("{}")
        assert validate_file(str(f)) is True

    def test_valid_json_array_returns_true(self, tmp_path):
        """JSON array is valid and returns True."""
        f = tmp_path / "array.json"
        f.write_text("[1, 2, 3]")
        assert validate_file(str(f)) is True

    def test_invalid_json_returns_false(self, tmp_path, capsys):
        """Malformed JSON returns False and prints ✗ with error."""
        f = tmp_path / "bad.json"
        f.write_text("{bad json}")
        assert validate_file(str(f)) is False
        captured = capsys.readouterr().out
        assert "✗" in captured
        assert str(f) in captured

    def test_missing_file_returns_false(self, capsys):
        """Non-existent file returns False and prints ✗."""
        assert validate_file("/nonexistent/file.json") is False
        assert "✗" in capsys.readouterr().out

    def test_invalid_json_trailing_comma(self, tmp_path):
        """JSON with trailing comma is invalid and returns False."""
        f = tmp_path / "trailing.json"
        f.write_text('{"key": "value",}')
        assert validate_file(str(f)) is False


class TestValidateJsonMain:
    """Tests for the main() entry point."""

    def test_no_files_returns_zero(self, capsys):
        """No files provided → prints message and returns 0."""
        result = main([])
        assert result == 0
        assert "No JSON files to validate" in capsys.readouterr().out

    def test_valid_file_returns_zero(self, tmp_path):
        """Single valid JSON file → returns 0."""
        f = tmp_path / "ok.json"
        f.write_text('{"status": "ok"}')
        assert main([str(f)]) == 0

    def test_invalid_file_returns_one(self, tmp_path):
        """Single invalid JSON file → returns 1."""
        f = tmp_path / "bad.json"
        f.write_text("not json at all {{")
        assert main([str(f)]) == 1

    def test_multiple_files_all_valid(self, tmp_path):
        """Multiple valid JSON files → returns 0."""
        for name, content in (("a.json", "{}"), ("b.json", "[1]")):
            (tmp_path / name).write_text(content)
        result = main([str(tmp_path / "a.json"), str(tmp_path / "b.json")])
        assert result == 0

    def test_multiple_files_one_bad_returns_one(self, tmp_path, capsys):
        """Mixed valid/invalid files → returns 1, prints both results."""
        (tmp_path / "good.json").write_text('{"ok": true}')
        (tmp_path / "bad.json").write_text("{oops}")
        result = main([str(tmp_path / "good.json"), str(tmp_path / "bad.json")])
        assert result == 1
        out = capsys.readouterr().out
        assert "✓" in out
        assert "✗" in out

    def test_empty_json_object_is_valid(self, tmp_path):
        """Explicit test that '{}' is treated as valid."""
        f = tmp_path / "empty.json"
        f.write_text("{}")
        assert main([str(f)]) == 0
