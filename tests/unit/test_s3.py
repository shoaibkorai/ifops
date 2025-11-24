"""
Unit tests for S3 commands.
"""

import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from ifops.main import app


class TestS3Commands:
    """Test cases for S3 commands."""

    def test_list_buckets(self, cli_runner, mock_boto3_client):
        """Test listing S3 buckets."""
        mock_client = MagicMock()
        mock_client.list_buckets.return_value = {
            "Buckets": [
                {"Name": "test-bucket-1", "CreationDate": "2024-01-01"},
                {"Name": "test-bucket-2", "CreationDate": "2024-01-02"}
            ]
        }
        mock_boto3_client.return_value = mock_client

        result = cli_runner.invoke(app, ["s3", "list"])
        assert result.exit_code == 0

    def test_create_bucket(self, cli_runner, mock_boto3_client):
        """Test creating an S3 bucket."""
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client

        result = cli_runner.invoke(app, ["s3", "create", "my-test-bucket"])
        assert result.exit_code == 0
