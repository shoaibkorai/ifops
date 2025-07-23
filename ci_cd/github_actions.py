import yaml
from utils.logger import setup_logger

logger = setup_logger()

def create_workflow(env: str):
    """Create a GitHub Actions workflow file."""
    with open("config/settings.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    repo = config["github"]["repo"]
    branch = config["github"]["branch"]
    
    workflow_content = f"""
name: CI/CD Pipeline for {env}
on:
  push:
    branches: [ {branch} ]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to {env}
        run: echo "Deploying to {env}"
"""
    with open(f".github/workflows/{env}-deploy.yml", "w") as f:
        f.write(workflow_content)
    
    logger.info(f"GitHub Actions workflow created for {env}")