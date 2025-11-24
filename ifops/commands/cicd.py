"""CI/CD pipeline management commands."""

import typer
import boto3
import json
from typing import Optional
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("ecr-push")
def push_to_ecr(
    repo: str = typer.Argument(..., help="ECR repository name"),
    tag: str = typer.Option("latest", "--tag", "-t", help="Image tag"),
    dockerfile: str = typer.Option("Dockerfile", "--dockerfile", "-f", help="Dockerfile path"),
    context: str = typer.Option(".", "--context", "-c", help="Build context path"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Build and push Docker image to ECR."""
    import subprocess

    ecr = boto3.client("ecr", region_name=region)
    sts = boto3.client("sts")

    try:
        # Get account ID and registry
        account_id = sts.get_caller_identity()["Account"]
        registry = f"{account_id}.dkr.ecr.{region}.amazonaws.com"
        full_image = f"{registry}/{repo}:{tag}"

        # Login to ECR using boto3
        console.print("[yellow]Logging in to ECR...[/yellow]")
        auth_response = ecr.get_authorization_token()
        auth_data = auth_response["authorizationData"][0]
        token = auth_data["authorizationToken"]

        # Decode and extract password
        import base64
        decoded = base64.b64decode(token).decode()
        password = decoded.split(":")[1]

        # Docker login
        login_cmd = f"docker login --username AWS --password {password} {registry}"
        subprocess.run(login_cmd, shell=True, check=True, capture_output=True)

        # Build image
        console.print(f"[yellow]Building image...[/yellow]")
        build_cmd = f"docker build -t {full_image} -f {dockerfile} {context}"
        subprocess.run(build_cmd, shell=True, check=True)

        # Push image
        console.print(f"[yellow]Pushing to ECR...[/yellow]")
        push_cmd = f"docker push {full_image}"
        subprocess.run(push_cmd, shell=True, check=True)

        console.print(f"[green]Successfully pushed {full_image}[/green]")

    except subprocess.CalledProcessError as e:
        console.print(f"[red]Command failed: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Failed to push to ECR: {e}[/red]")
        raise typer.Exit(1)


@app.command("deploy-apprunner")
def deploy_to_apprunner(
    service_arn: str = typer.Argument(..., help="App Runner service ARN"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Trigger deployment to App Runner."""
    client = boto3.client("apprunner", region_name=region)

    try:
        response = client.start_deployment(ServiceArn=service_arn)
        console.print(f"[green]Deployment triggered: {response['OperationId']}[/green]")

    except Exception as e:
        console.print(f"[red]Failed to deploy: {e}[/red]")
        raise typer.Exit(1)


@app.command("deploy-ecs")
def deploy_to_ecs(
    cluster: str = typer.Argument(..., help="ECS cluster name"),
    service: str = typer.Option(..., "--service", "-s", help="ECS service name"),
    task_definition: str = typer.Option(None, "--task-def", "-t", help="New task definition"),
    force: bool = typer.Option(True, "--force/--no-force", help="Force new deployment"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Deploy to ECS service."""
    client = boto3.client("ecs", region_name=region)

    try:
        params = {
            "cluster": cluster,
            "service": service,
            "forceNewDeployment": force
        }

        if task_definition:
            params["taskDefinition"] = task_definition

        response = client.update_service(**params)
        deployment = response["service"]["deployments"][0]

        console.print(f"[green]Deployment started: {deployment['id']}[/green]")
        console.print(f"Task Definition: {deployment['taskDefinition']}")
        console.print(f"Status: {deployment['status']}")

    except Exception as e:
        console.print(f"[red]Failed to deploy: {e}[/red]")
        raise typer.Exit(1)


@app.command("deploy-amplify")
def deploy_to_amplify(
    app_id: str = typer.Argument(..., help="Amplify app ID"),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch to deploy"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Deploy to Amplify."""
    client = boto3.client("amplify", region_name=region)

    try:
        response = client.start_job(
            appId=app_id,
            branchName=branch,
            jobType="RELEASE"
        )

        job = response["jobSummary"]
        console.print(f"[green]Deployment started![/green]")
        console.print(f"Job ID: {job['jobId']}")
        console.print(f"Status: {job['status']}")

    except Exception as e:
        console.print(f"[red]Failed to deploy: {e}[/red]")
        raise typer.Exit(1)


@app.command("deploy-s3")
def deploy_to_s3(
    bucket: str = typer.Argument(..., help="S3 bucket name"),
    source: str = typer.Option(..., "--source", "-s", help="Local directory to deploy"),
    distribution_id: str = typer.Option(None, "--cf-dist", help="CloudFront distribution ID to invalidate"),
    delete: bool = typer.Option(True, "--delete/--no-delete", help="Delete files not in source"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Deploy static site to S3."""
    import os
    import mimetypes

    s3 = boto3.client("s3", region_name=region)

    try:
        # Get list of existing objects if delete is enabled
        existing_keys = set()
        if delete:
            paginator = s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket):
                for obj in page.get("Contents", []):
                    existing_keys.add(obj["Key"])

        # Upload files
        console.print(f"[yellow]Syncing to S3...[/yellow]")
        uploaded_keys = set()

        for root, dirs, files in os.walk(source):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, source)
                s3_key = relative_path.replace(os.sep, "/")

                # Determine content type
                content_type, _ = mimetypes.guess_type(file)
                extra_args = {}
                if content_type:
                    extra_args["ContentType"] = content_type

                s3.upload_file(local_path, bucket, s3_key, ExtraArgs=extra_args)
                uploaded_keys.add(s3_key)
                console.print(f"  Uploaded: {s3_key}")

        # Delete files not in source
        if delete:
            keys_to_delete = existing_keys - uploaded_keys
            if keys_to_delete:
                console.print(f"[yellow]Deleting {len(keys_to_delete)} old files...[/yellow]")
                for key in keys_to_delete:
                    s3.delete_object(Bucket=bucket, Key=key)
                    console.print(f"  Deleted: {key}")

        console.print(f"[green]Files synced to {bucket}[/green]")

        # Invalidate CloudFront cache if provided
        if distribution_id:
            console.print(f"[yellow]Invalidating CloudFront cache...[/yellow]")
            cf = boto3.client("cloudfront")
            import time
            cf.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    "Paths": {
                        "Quantity": 1,
                        "Items": ["/*"]
                    },
                    "CallerReference": str(int(time.time()))
                }
            )
            console.print(f"[green]CloudFront cache invalidated[/green]")

    except Exception as e:
        console.print(f"[red]Failed to deploy: {e}[/red]")
        raise typer.Exit(1)


@app.command("create-pipeline")
def create_codepipeline(
    name: str = typer.Argument(..., help="Pipeline name"),
    repo: str = typer.Option(..., "--repo", "-r", help="GitHub repository (owner/repo)"),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch to watch"),
    connection_arn: str = typer.Option(..., "--connection", help="CodeStar connection ARN"),
    ecr_repo: str = typer.Option(..., "--ecr", help="ECR repository name"),
    cluster: str = typer.Option(..., "--cluster", help="ECS cluster name"),
    service: str = typer.Option(..., "--service", help="ECS service name"),
    role_arn: str = typer.Option(..., "--role", help="Pipeline service role ARN"),
    artifact_bucket: str = typer.Option(..., "--artifact-bucket", help="S3 bucket for artifacts"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Create a CodePipeline for CI/CD."""
    client = boto3.client("codepipeline", region_name=region)
    sts = boto3.client("sts")

    try:
        account_id = sts.get_caller_identity()["Account"]

        pipeline_config = {
            "name": name,
            "roleArn": role_arn,
            "artifactStore": {
                "type": "S3",
                "location": artifact_bucket
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
                                "provider": "CodeStarSourceConnection",
                                "version": "1"
                            },
                            "configuration": {
                                "ConnectionArn": connection_arn,
                                "FullRepositoryId": repo,
                                "BranchName": branch
                            },
                            "outputArtifacts": [{"name": "SourceOutput"}]
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
                                "ProjectName": f"{name}-build"
                            },
                            "inputArtifacts": [{"name": "SourceOutput"}],
                            "outputArtifacts": [{"name": "BuildOutput"}]
                        }
                    ]
                },
                {
                    "name": "Deploy",
                    "actions": [
                        {
                            "name": "Deploy",
                            "actionTypeId": {
                                "category": "Deploy",
                                "owner": "AWS",
                                "provider": "ECS",
                                "version": "1"
                            },
                            "configuration": {
                                "ClusterName": cluster,
                                "ServiceName": service,
                                "FileName": "imagedefinitions.json"
                            },
                            "inputArtifacts": [{"name": "BuildOutput"}]
                        }
                    ]
                }
            ]
        }

        response = client.create_pipeline(pipeline=pipeline_config)
        console.print(f"[green]Pipeline '{name}' created successfully![/green]")
        console.print(f"ARN: {response['pipeline']['name']}")

    except Exception as e:
        console.print(f"[red]Failed to create pipeline: {e}[/red]")
        raise typer.Exit(1)


@app.command("list-pipelines")
def list_pipelines(
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """List CodePipelines."""
    client = boto3.client("codepipeline", region_name=region)

    try:
        response = client.list_pipelines()

        table = Table(title="CodePipelines")
        table.add_column("Name", style="cyan")
        table.add_column("Created", style="dim")
        table.add_column("Updated", style="dim")

        for pipeline in response.get("pipelines", []):
            table.add_row(
                pipeline["name"],
                str(pipeline.get("created", "N/A")),
                str(pipeline.get("updated", "N/A"))
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list pipelines: {e}[/red]")
        raise typer.Exit(1)


@app.command("trigger")
def trigger_pipeline(
    name: str = typer.Argument(..., help="Pipeline name"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Trigger a pipeline execution."""
    client = boto3.client("codepipeline", region_name=region)

    try:
        response = client.start_pipeline_execution(name=name)
        console.print(f"[green]Pipeline execution started: {response['pipelineExecutionId']}[/green]")

    except Exception as e:
        console.print(f"[red]Failed to trigger pipeline: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
def pipeline_status(
    name: str = typer.Argument(..., help="Pipeline name"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Get pipeline execution status."""
    client = boto3.client("codepipeline", region_name=region)

    try:
        response = client.get_pipeline_state(name=name)

        console.print(f"[bold]Pipeline: {name}[/bold]")

        for stage in response.get("stageStates", []):
            status = stage.get("latestExecution", {}).get("status", "N/A")
            color = "green" if status == "Succeeded" else "yellow" if status == "InProgress" else "red"
            console.print(f"  {stage['stageName']}: [{color}]{status}[/{color}]")

    except Exception as e:
        console.print(f"[red]Failed to get status: {e}[/red]")
        raise typer.Exit(1)
