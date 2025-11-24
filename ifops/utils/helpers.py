"""
Helper utilities for IFOps CLI.
"""

from datetime import datetime
from typing import Optional
import typer


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_datetime(dt: datetime) -> str:
    """Format datetime to readable string."""
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def confirm_action(message: str, default: bool = False) -> bool:
    """Prompt user for confirmation."""
    return typer.confirm(message, default=default)


def truncate_string(s: str, max_length: int = 50) -> str:
    """Truncate string with ellipsis."""
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."


def parse_tags(tags_str: str) -> dict:
    """Parse tags string (key=value,key2=value2) to dict."""
    if not tags_str:
        return {}

    tags = {}
    for pair in tags_str.split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            tags[key.strip()] = value.strip()
    return tags


def tags_to_aws_format(tags: dict) -> list:
    """Convert dict tags to AWS format."""
    return [{"Key": k, "Value": v} for k, v in tags.items()]


def aws_tags_to_dict(aws_tags: list) -> dict:
    """Convert AWS format tags to dict."""
    return {tag["Key"]: tag["Value"] for tag in aws_tags}
