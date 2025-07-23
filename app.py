import typer
from infrastructure.aws.functions import amplify, ec2, ecs, rds, s3, vpc
# from ci_cd import github_actions, codepipeline
# from ssl import acm, letsencrypt
# from config_mgmt import ssm, ansible_runner
from utils.logger import setup_logger

app = typer.Typer()
logger = setup_logger()

# Infrastructure Commands
@app.command()
def create_infra(env: str = "dev"):
    """Create AWS infrastructure for the specified environment."""
    logger.info(f"Creating infrastructure for {env} environment")
    vpc.create_vpc(env)
    ec2.create_ec2_instance(env)
    s3.create_s3_bucket(env)
    rds.create_rds_instance(env)
    typer.echo(f"Infrastructure created for {env}")

@app.command()
def create_ec2(env: str = "dev"):
    """Create only an EC2 instance for the specified environment."""
    logger.info(f"Creating EC2 instance for {env} environment")
    ec2.create_ec2_instance(env)
    typer.echo(f"EC2 instance created for {env}")

@app.command()
def create_s3(env: str = "dev"):
    """Create only an S3 bucket for the specified environment."""
    logger.info(f"Creating S3 bucket for {env} environment")
    s3.create_s3_bucket(env)
    typer.echo(f"S3 bucket created for {env}")

@app.command()
def create_rds(env: str = "dev"):
    """Create only an RDS instance for the specified environment."""
    logger.info(f"Creating RDS instance for {env} environment")
    rds.create_rds_instance(env)
    typer.echo(f"RDS instance created for {env}")

@app.command()
def create_vpc(env: str = "dev"):
    """Create only a VPC for the specified environment."""
    logger.info(f"Creating VPC for {env} environment")
    vpc.create_vpc(env)
    typer.echo(f"VPC created for {env}")

@app.command()
def create_amplify(env: str = "dev"):
    """Create only an Amplify environment for the specified environment."""
    logger.info(f"Creating Amplify for {env} environment")
    amplify.create_amplify(env)
    typer.echo(f"Amplify created for {env}")

@app.command()
def create_ecs(env: str = "dev"):
    """Create only an ECS cluster for the specified environment."""
    logger.info(f"Creating ECS cluster for {env} environment")
    ecs.create_ecs(env)
    typer.echo(f"ECS cluster created for {env}")

# CI/CD Commands
@app.command()
def setup_ci_cd(env: str = "dev"):
    """Set up CI/CD pipeline."""
    logger.info(f"Setting up CI/CD for {env}")
    github_actions.create_workflow(env)
    codepipeline.create_pipeline(env)
    typer.echo(f"CI/CD pipeline set up for {env}")

# SSL Commands
@app.command()
def setup_ssl(domain: str, env: str = "dev"):
    """Set up SSL certificates."""
    logger.info(f"Setting up SSL for {domain} in {env}")
    acm.request_acm_certificate(domain)
    letsencrypt.request_letsencrypt_certificate(domain)
    typer.echo(f"SSL setup completed for {domain}")

# Config Management Commands
@app.command()
def configure_instance(env: str = "dev"):
    """Configure instances using SSM and Ansible."""
    logger.info(f"Configuring instances for {env}")
    ssm.store_parameter(env)
    ansible_runner.run_ansible_playbook()
    typer.echo(f"Instance configuration completed for {env}")

if __name__ == "__main__":
    app()