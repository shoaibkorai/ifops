import boto3
from utils.aws_helpers import get_aws_session
from utils.logger import setup_logger

logger = setup_logger()

def store_parameter(env: str):
    """Store configuration in AWS SSM Parameter Store."""
    session = get_aws_session()
    ssm = session.client("ssm")
    
    param_name = f"/myapp/{env}/config"
    param_value = "example-config-value"
    
    logger.info(f"Storing SSM parameter {param_name}")
    ssm.put_parameter(
        Name=param_name,
        Value=param_value,
        Type="String",
        Overwrite=True
    )
    logger.info(f"SSM parameter {param_name} stored")