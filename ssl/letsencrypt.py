import subprocess
from utils.logger import setup_logger

logger = setup_logger()

def request_letsencrypt_certificate(domain: str):
    """Request a Let's Encrypt certificate using certbot."""
    logger.info(f"Requesting Let's Encrypt certificate for {domain}")
    try:
        subprocess.run([
            "certbot", "certonly", "--standalone",
            "-d", domain, "--non-interactive", "--agree-tos",
            "-m", "admin@example.com"
        ], check=True)
        logger.info(f"Let's Encrypt certificate obtained for {domain}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to obtain Let's Encrypt certificate: {e}")