import boto3
from utils.aws_helpers import get_aws_session
from utils.logger import setup_logger

logger = setup_logger()

def create_pipeline(env: str):
    """Create an AWS CodePipeline."""
    session = get_aws_session()
    codepipeline = session.client("codepipeline")
    
    pipeline = {
        "name": f"myapp-{env}-pipeline",
        "roleArn": "arn:aws:iam::ACCOUNT_ID:role/CodePipelineRole",  # Replace ACCOUNT_ID
        "artifactStore": {
            "type": "S3",
            "location": f"myapp-{env}-artifacts"
        },
        "stages": [
            {
                "name": "Source",
                "actions": [
                    {
                        "name": "Source",
                        "actionTypeId": {
                            "category": "Source",
                            "owner": "AWS",
                            "provider": "CodeCommit",
                            "version": "1"
                        },
                        "configuration": {
                            "BranchName": "main",
                            "RepositoryName": f"myapp-{env}"
                        },
                        "outputArtifacts": [{"name": "SourceArtifact"}]
                    }
                ]
            },
            {
                "name": "Build",
                "actions": [
                    {
                        "name": "Build",
                        "actionTypeId": {
                            "category": "Build",
                            "owner": "AWS",
                            "provider": "CodeBuild",
                            "version": "1"
                        },
                        "configuration": {
                            "ProjectName": f"myapp-{env}-build"
                        },
                        "inputArtifacts": [{"name": "SourceArtifact"}],
                        "output artifacts": [{"name": "BuildArtifact"}]
                    }
                ]
            }
        ]
    }
    
    logger.info(f"Creating CodePipeline for {env}")
    codepipeline.create_pipeline(pipeline=pipeline)
    logger.info(f"CodePipeline myapp-{env}-pipeline created")