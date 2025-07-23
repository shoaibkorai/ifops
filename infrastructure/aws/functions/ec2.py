import boto3
import yaml
from utils.aws_helpers import get_aws_session
from utils.logger import setup_logger

logger = setup_logger()

def create_ec2_instance(env: str):
    """Create an EC2 instance."""
    with open("config/settings.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    session = get_aws_session()
    ec2 = session.resource("ec2")
    instance_type = config["environments"][env]["ec2_instance_type"]
    
    logger.info(f"Creating EC2 instance in {env} with type {instance_type}")
    instances = ec2.create_instances(
        ImageId="ami-014e30c8a36252ae5",  
        InstanceType=instance_type,
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Environment", "Value": env}]
        }]
    )
    logger.info(f"Created EC2 instance: {instances[0].id}")