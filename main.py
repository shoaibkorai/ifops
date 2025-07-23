import typer
from infrastructure import ec2, s3, rds, vpc
from ci_cd import github_actions, codepipeline
from ssl import acm, letsencrypt
from config_mgmt import ssm, ansible_runner
from utils.logger import setup_logger

app = typer.Typer()
logger = setup_logger()

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
def setup_ci_cd(env: str = "dev"):
    """Set up CI/CD pipeline."""
    logger.info(f"Setting up CI/CD for {env}")
    github_actions.create_workflow(env)
    codepipeline.create_pipeline(env)
    typer.echo(f"CI/CD pipeline set up for {env}")

@app.command()
def setup_ssl(domain: str, env: str = "dev"):
    """Set up SSL certificates."""
    logger.info(f"Setting up SSL for {domain} in {env}")
    acm.request_acm_certificate(domain)
    letsencrypt.request_letsencrypt_certificate(domain)
    typer.echo(f"SSL setup completed for {domain}")

@app.command()
def configure_instance(env: str = "dev"):
    """Configure instances using SSM and Ansible."""
    logger.info(f"Configuring instances for {env}")
    ssm.store_parameter(env)
    ansible_runner.run_ansible_playbook()
    typer.echo(f"Instance configuration completed for {env}")

if __name__ == "__main__":
    app()

