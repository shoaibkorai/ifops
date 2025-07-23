import boto3
import yaml
from utils.aws_helpers import get_aws_session
from utils.logger import setup_logger

logger = setup_logger()

def create_rds_instance(env: str):
    """Create an RDS instance."""
    with open("config/settings.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    session = get_aws_session()
    rds = session.client("rds")
    instance_type = config["environments"][env]["rds_instance_type"]
    
    logger.info(f"Creating RDS instance in {env} with type {instance_type}")
    rds.create_db_instance(
        DBInstanceIdentifier=f"myapp-{env}-db",
        AllocatedStorage=20,
        DBInstanceClass=instance_type,
        Engine="mysql",
        MasterUsername="admin",
        MasterUserPassword="securepassword123",
        Tags=[{"Key": "Environment", "Value": env}]
    )
    logger.info(f"RDS instance myapp-{env}-db created")