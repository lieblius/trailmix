"""Tests for config module."""

from pathlib import Path
from unittest.mock import patch

from trailmix.config import (
    get_meetings_dir,
    load_config,
    save_config,
    set_meetings_dir,
)


def test_load_config_missing(tmp_path):
    """Test loading config when file doesn't exist."""
    with patch("trailmix.config.CONFIG_DIR", tmp_path):
        config = load_config()
        assert config == {}


def test_save_and_load_config(tmp_path):
    """Test saving and loading config."""
    with patch("trailmix.config.CONFIG_DIR", tmp_path):
        save_config({"meetings_dir": "/test/path"})
        config = load_config()
        assert config["meetings_dir"] == "/test/path"


def test_get_meetings_dir_not_configured(tmp_path):
    """Test get_meetings_dir when not configured."""
    with patch("trailmix.config.CONFIG_DIR", tmp_path):
        result = get_meetings_dir()
        assert result is None


def test_get_meetings_dir_configured(tmp_path):
    """Test get_meetings_dir when configured."""
    with patch("trailmix.config.CONFIG_DIR", tmp_path):
        save_config({"meetings_dir": "/test/meetings"})
        result = get_meetings_dir()
        assert result == Path("/test/meetings")


def test_set_meetings_dir(tmp_path):
    """Test set_meetings_dir."""
    with patch("trailmix.config.CONFIG_DIR", tmp_path):
        test_path = tmp_path / "meetings"
        test_path.mkdir()
        set_meetings_dir(test_path)

        config = load_config()
        assert config["meetings_dir"] == str(test_path.resolve())
