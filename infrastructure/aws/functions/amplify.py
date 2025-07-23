import boto3
import yaml
from utils.aws_helpers import get_aws_session
from utils.logger import setup_logger

logger = setup_logger()

def create_amplify(env: str):
    """Create an Amplify app for the specified environment."""
    with open("config/settings.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    session = get_aws_session()
    amplify = session.client("amplify")
    app_name = config["environments"][env]["amplify_app_name"]
    repository = config["environments"][env]["amplify_repository"]
    oauth_token = config["environments"][env]["amplify_oauth_token"]
    
    logger.info(f"Creating Amplify app {app_name} for {env} environment")
    response = amplify.create_app(
        name=app_name,
        repository=repository,
        oauthToken=oauth_token,
        environmentVariables={
            "ENV": env
        },
        buildSpec="version: 1\nfrontend:\n  phases:\n    build:\n      commands: ['npm run build']\n  artifacts:\n    baseDirectory: build\n    files: '**/*'"
    )
    app_id = response["app"]["appId"]
    logger.info(f"Amplify app {app_name} created with App ID {app_id}")
    
    # Create a branch (e.g., main) for the app
    amplify.create_branch(
        appId=app_id,
        branchName="main",
        enableAutoBuild=True
    )
    logger.info(f"Amplify branch 'main' created for app {app_id}")