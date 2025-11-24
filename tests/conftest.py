"""
Pytest configuration and fixtures.
"""

import pytest
from typer.testing import CliRunner
from unittest.mock import MagicMock, patch


@pytest.fixture
def cli_runner():
    """Provide a CLI runner for testing commands."""
    return CliRunner()


@pytest.fixture
def mock_boto3_client():
    """Provide a mock boto3 client."""
    with patch("boto3.client") as mock:
        yield mock


@pytest.fixture
def mock_boto3_resource():
    """Provide a mock boto3 resource."""
    with patch("boto3.resource") as mock:
        yield mock


@pytest.fixture
def sample_ec2_instance():
    """Sample EC2 instance data."""
    return {
        "InstanceId": "i-1234567890abcdef0",
        "InstanceType": "t3.micro",
        "State": {"Name": "running"},
        "PublicIpAddress": "54.123.45.67",
        "PrivateIpAddress": "10.0.1.100",
        "Tags": [{"Key": "Name", "Value": "test-instance"}],
        "LaunchTime": "2024-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_s3_bucket():
    """Sample S3 bucket data."""
    return {
        "Name": "test-bucket",
        "CreationDate": "2024-01-01T00:00:00Z"
    }
