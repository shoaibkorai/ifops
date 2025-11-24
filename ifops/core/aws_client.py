"""
AWS client factory for creating boto3 clients with proper configuration.
"""

import boto3
from typing import Optional
from .config import get_aws_region, get_aws_profile


class AWSClientFactory:
    """Factory for creating configured AWS clients."""

    _session = None

    @classmethod
    def get_session(cls, profile: Optional[str] = None, region: Optional[str] = None):
        """Get or create a boto3 session."""
        profile = profile or get_aws_profile()
        region = region or get_aws_region()

        session_kwargs = {}
        if profile:
            session_kwargs["profile_name"] = profile
        if region:
            session_kwargs["region_name"] = region

        return boto3.Session(**session_kwargs)

    @classmethod
    def get_client(cls, service: str, region: Optional[str] = None, profile: Optional[str] = None):
        """Get a boto3 client for the specified service."""
        session = cls.get_session(profile=profile, region=region)
        return session.client(service, region_name=region or get_aws_region())

    @classmethod
    def get_resource(cls, service: str, region: Optional[str] = None, profile: Optional[str] = None):
        """Get a boto3 resource for the specified service."""
        session = cls.get_session(profile=profile, region=region)
        return session.resource(service, region_name=region or get_aws_region())


# Convenience functions
def get_client(service: str, region: Optional[str] = None):
    """Get a boto3 client for the specified service."""
    return AWSClientFactory.get_client(service, region=region)


def get_resource(service: str, region: Optional[str] = None):
    """Get a boto3 resource for the specified service."""
    return AWSClientFactory.get_resource(service, region=region)
