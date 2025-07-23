import boto3
import yaml
from utils.aws_helpers import get_aws_session
from utils.logger import setup_logger

logger = setup_logger()

def create_vpc(env: str):
    """Create a VPC."""
    with open("config/settings.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    session = get_aws_session()
    ec2 = session.client("ec2")
    cidr_block = config["environments"][env]["vpc_cidr"]
    
    logger.info(f"Creating VPC with CIDR {cidr_block}")
    response = ec2.create_vpc(CidrBlock=cidr_block)
    vpc_id = response["Vpc"]["VpcId"]
    ec2.create_tags(
        Resources=[vpc_id],
        Tags=[{"Key": "Environment", "Value": env}]
    )
    logger.info(f"VPC {vpc_id} created")