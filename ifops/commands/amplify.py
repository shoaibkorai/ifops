"""Amplify deployment management commands."""

import typer
import boto3
from typing import Optional
from rich.console import Console
from rich.table import Table

from ifops.core.config import handle_profile_param

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.callback()
def amplify_callback(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile to use")
):
    """Amplify deployment management."""
    handle_profile_param(profile)


@app.command("create")
def create_app(
    name: str = typer.Argument(..., help="Application name"),
    repository: str = typer.Option(..., "--repo", "-r", help="Git repository URL"),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch to deploy"),
    access_token: str = typer.Option(None, "--token", "-t", help="Git access token"),
    build_spec: str = typer.Option(None, "--build-spec", help="Path to buildspec.yml"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Create a new Amplify application."""
    client = boto3.client("amplify", region_name=region)

    try:
        app_params = {
            "name": name,
            "repository": repository,
        }

        if access_token:
            app_params["accessToken"] = access_token

        if build_spec:
            with open(build_spec, "r") as f:
                app_params["buildSpec"] = f.read()

        response = client.create_app(**app_params)
        app_info = response["app"]

        console.print(f"[green]Amplify app '{name}' created successfully![/green]")
        console.print(f"App ID: {app_info['appId']}")
        console.print(f"Default Domain: {app_info['defaultDomain']}")

        # Create branch
        branch_response = client.create_branch(
            appId=app_info["appId"],
            branchName=branch,
            enableAutoBuild=True
        )
        console.print(f"[green]Branch '{branch}' configured for auto-build[/green]")

    except Exception as e:
        console.print(f"[red]Failed to create Amplify app: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_apps(
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """List all Amplify applications."""
    client = boto3.client("amplify", region_name=region)

    try:
        response = client.list_apps()

        table = Table(title="Amplify Applications")
        table.add_column("Name", style="cyan")
        table.add_column("App ID", style="dim")
        table.add_column("Repository", style="blue")
        table.add_column("Default Domain", style="green")

        for app_info in response.get("apps", []):
            table.add_row(
                app_info["name"],
                app_info["appId"],
                app_info.get("repository", "N/A"),
                app_info["defaultDomain"]
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list apps: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_app(
    app_id: str = typer.Argument(..., help="App ID to delete"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Delete an Amplify application."""
    client = boto3.client("amplify", region_name=region)

    try:
        client.delete_app(appId=app_id)
        console.print(f"[green]Amplify app '{app_id}' deleted successfully![/green]")

    except Exception as e:
        console.print(f"[red]Failed to delete app: {e}[/red]")
        raise typer.Exit(1)


@app.command("deploy")
def start_deployment(
    app_id: str = typer.Argument(..., help="App ID"),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch to deploy"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Start a new deployment for an Amplify branch."""
    client = boto3.client("amplify", region_name=region)

    try:
        response = client.start_job(
            appId=app_id,
            branchName=branch,
            jobType="RELEASE"
        )

        job_summary = response["jobSummary"]
        console.print(f"[green]Deployment started![/green]")
        console.print(f"Job ID: {job_summary['jobId']}")
        console.print(f"Status: {job_summary['status']}")

    except Exception as e:
        console.print(f"[red]Failed to start deployment: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
def deployment_status(
    app_id: str = typer.Argument(..., help="App ID"),
    branch: str = typer.Option("main", "--branch", "-b", help="Branch name"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Get deployment status for an Amplify branch."""
    client = boto3.client("amplify", region_name=region)

    try:
        response = client.list_jobs(
            appId=app_id,
            branchName=branch,
            maxResults=5
        )

        table = Table(title=f"Recent Deployments - {branch}")
        table.add_column("Job ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Started", style="dim")
        table.add_column("Ended", style="dim")

        for job in response.get("jobSummaries", []):
            table.add_row(
                job["jobId"],
                job["status"],
                str(job.get("startTime", "N/A")),
                str(job.get("endTime", "N/A"))
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to get deployment status: {e}[/red]")
        raise typer.Exit(1)


@app.command("domain")
def add_domain(
    app_id: str = typer.Argument(..., help="App ID"),
    domain: str = typer.Option(..., "--domain", "-d", help="Custom domain name"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Add a custom domain to an Amplify app."""
    client = boto3.client("amplify", region_name=region)

    try:
        response = client.create_domain_association(
            appId=app_id,
            domainName=domain,
            subDomainSettings=[
                {
                    "prefix": "",
                    "branchName": "main"
                },
                {
                    "prefix": "www",
                    "branchName": "main"
                }
            ]
        )

        console.print(f"[green]Domain association created for {domain}[/green]")
        console.print(f"Certificate verification: {response['domainAssociation']['certificateVerificationDNSRecord']}")

    except Exception as e:
        console.print(f"[red]Failed to add domain: {e}[/red]")
        raise typer.Exit(1)
