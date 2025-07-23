import boto3
import yaml
from utils.aws_helpers import get_aws_session
from utils.logger import setup_logger

logger = setup_logger()

def create_s3_bucket(env: str):
    """Create an S3 bucket."""
    with open("config/settings.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    session = get_aws_session()
    s3 = session.client("s3")
    bucket_name = f"{config['environments'][env]['bucket_prefix']}-bucket"
    
    logger.info(f"Creating S3 bucket: {bucket_name}")
    s3.create_bucket(Bucket=bucket_name)
    logger.info(f"S3 bucket {bucket_name} created")