import boto3
import yaml
import os
from utils.logger import setup_logger

logger = setup_logger()

def get_aws_session():
    """Create a Boto3 session using credentials from YAML or environment."""
    # Try to load credentials from credentials/aws_credentials.yaml
    try:
        with open("credentials/vault.yaml", "r") as f:
            creds = yaml.safe_load(f)
        aws_access_key_id = creds.get("aws", {}).get("access_key_id")
        aws_secret_access_key = creds.get("aws", {}).get("secret_access_key")
        aws_region = creds.get("aws", {}).get("region", "us-east-1")
        
        if aws_access_key_id and aws_secret_access_key:
            logger.info(f"Using credentials from credentials/vault.yaml in region {aws_region}")
            return boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_region
            )
    except FileNotFoundError:
        logger.warning("credentials/aws_credentials.yaml not found, falling back to other methods")
    
    # Fallback to AWS profile or environment variables
    try:
        with open("config/settings.yaml", "r") as f:
            config = yaml.safe_load(f)
        aws_profile = config.get("aws", {}).get("profile", "default")
        aws_region = config.get("aws", {}).get("region", "us-east-1")
        
        logger.info(f"Using AWS profile {aws_profile} in region {aws_region}")
        return boto3.Session(profile_name=aws_profile, region_name=aws_region)
    except Exception as e:
        logger.warning(f"Failed to use AWS profile, falling back to environment variables: {e}")
    
    # Fallback to environment variables or IAM role
    aws_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    logger.info(f"Using environment variables or IAM role in region {aws_region}")
    return boto3.Session(region_name=aws_region)


