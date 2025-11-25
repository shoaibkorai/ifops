"""
Configuration management for IFOps CLI.
"""

import os
from pathlib import Path
from typing import Optional
import yaml
import configparser

# Default configuration
DEFAULT_CONFIG = {
    "aws": {
        "region": "us-east-1",
        "profile": "default"
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
}

# Config file locations
CONFIG_DIR = Path.home() / ".ifops"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
CREDENTIALS_FILE = CONFIG_DIR / "credentials"


def get_config_dir() -> Path:
    """Get or create the configuration directory."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_config() -> dict:
    """Load configuration from file or return defaults."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            user_config = yaml.safe_load(f) or {}
            # Merge with defaults
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            return config
    return DEFAULT_CONFIG


def save_config(config: dict) -> None:
    """Save configuration to file."""
    get_config_dir()
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def load_credentials(profile: str = "default") -> dict:
    """Load credentials for a specific profile."""
    if not CREDENTIALS_FILE.exists():
        return {}

    config = configparser.ConfigParser()
    config.read(CREDENTIALS_FILE)

    if profile in config:
        return {
            "aws_access_key_id": config[profile].get("aws_access_key_id", ""),
            "aws_secret_access_key": config[profile].get("aws_secret_access_key", ""),
            "region": config[profile].get("region", "us-east-1")
        }
    return {}


def save_credentials(profile: str, access_key: str, secret_key: str, region: str) -> None:
    """Save credentials for a profile."""
    get_config_dir()

    config = configparser.ConfigParser()
    if CREDENTIALS_FILE.exists():
        config.read(CREDENTIALS_FILE)

    config[profile] = {
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "region": region
    }

    with open(CREDENTIALS_FILE, "w") as f:
        config.write(f)

    # Set secure permissions
    os.chmod(CREDENTIALS_FILE, 0o600)


def list_profiles() -> list:
    """List all configured profiles."""
    if not CREDENTIALS_FILE.exists():
        return []

    config = configparser.ConfigParser()
    config.read(CREDENTIALS_FILE)
    return list(config.sections())


def get_aws_region() -> str:
    """Get AWS region from config or environment."""
    return os.environ.get("AWS_DEFAULT_REGION") or load_config()["aws"]["region"]


def get_aws_profile() -> Optional[str]:
    """Get AWS profile from config or environment."""
    return os.environ.get("AWS_PROFILE") or load_config()["aws"].get("profile")


def apply_profile(profile: str) -> None:
    """Apply credentials from a profile to environment."""
    creds = load_credentials(profile)
    if creds:
        os.environ["AWS_ACCESS_KEY_ID"] = creds["aws_access_key_id"]
        os.environ["AWS_SECRET_ACCESS_KEY"] = creds["aws_secret_access_key"]
        if creds.get("region"):
            os.environ["AWS_DEFAULT_REGION"] = creds["region"]


def handle_profile_param(profile: Optional[str]) -> None:
    """
    Handle profile parameter in commands.
    This allows --profile to work both globally and per-command.
    """
    if profile:
        creds = load_credentials(profile)
        if creds:
            apply_profile(profile)
        else:
            from rich.console import Console
            console = Console()
            console.print(f"[red]Profile '{profile}' not found in {CREDENTIALS_FILE}[/red]")
            console.print(f"Available profiles: {', '.join(list_profiles()) or 'none'}")
            import typer
            raise typer.Exit(1)
