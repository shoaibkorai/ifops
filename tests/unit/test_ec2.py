"""
Unit tests for EC2 commands.
"""

import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from ifops.main import app


class TestEC2Commands:
    """Test cases for EC2 commands."""

    def test_list_instances_empty(self, cli_runner, mock_boto3_client):
        """Test listing instances when none exist."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {"Reservations": []}
        mock_boto3_client.return_value = mock_client

        result = cli_runner.invoke(app, ["ec2", "list"])
        assert result.exit_code == 0

    def test_list_instances_with_data(self, cli_runner, mock_boto3_client, sample_ec2_instance):
        """Test listing instances with data."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [{"Instances": [sample_ec2_instance]}]
        }
        mock_boto3_client.return_value = mock_client

        result = cli_runner.invoke(app, ["ec2", "list"])
        assert result.exit_code == 0


class TestEC2Validation:
    """Test input validation for EC2 commands."""

    def test_create_requires_ami(self, cli_runner):
        """Test that create command requires AMI."""
        result = cli_runner.invoke(app, ["ec2", "create", "test-instance"])
        assert result.exit_code != 0
        assert "ami" in result.output.lower() or "required" in result.output.lower()
