import boto3
from utils.aws_helpers import get_aws_session
from utils.logger import setup_logger

logger = setup_logger()

def request_acm_certificate(domain: str):
    """Request an SSL certificate from AWS ACM."""
    session = get_aws_session()
    acm = session.client("acm")
    
    logger.info(f"Requesting ACM certificate for {domain}")
    response = acm.request_certificate(
        DomainName=domain,
        ValidationMethod="DNS",
        Tags=[{"Key": "Environment", "Value": "dev"}]
    )
    logger.info(f"ACM certificate requested: {response['CertificateArn']}")