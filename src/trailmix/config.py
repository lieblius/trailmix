"""Configuration management for trailmix."""

import tomllib
from pathlib import Path

import tomli_w

CONFIG_DIR = Path.home() / ".config" / "trailmix"
CONFIG_FILE = "config.toml"


class ConfigError(Exception):
    """Configuration error."""

    pass


def get_config_path() -> Path:
    """Get the path to the config file."""
    return CONFIG_DIR / CONFIG_FILE


def load_config() -> dict:
    """Load the config file. Returns empty dict if not found."""
    config_path = get_config_path()

    if not config_path.exists():
        return {}

    with open(config_path, "rb") as f:
        return tomllib.load(f)


def save_config(config: dict) -> None:
    """Save the config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_path = get_config_path()

    with open(config_path, "wb") as f:
        tomli_w.dump(config, f)


def get_meetings_dir() -> Path | None:
    """Get the configured meetings directory. Returns None if not configured."""
    config = load_config()
    meetings_dir = config.get("meetings_dir")

    if not meetings_dir:
        return None

    return Path(meetings_dir)


def set_meetings_dir(path: Path) -> None:
    """Set the meetings directory in config."""
    config = load_config()
    config["meetings_dir"] = str(path.resolve())
    save_config(config)
