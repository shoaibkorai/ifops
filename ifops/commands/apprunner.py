"""App Runner deployment management commands."""

import typer
import boto3
from typing import Optional
from rich.console import Console
from rich.table import Table

from ifops.core.config import handle_profile_param

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.callback()
def apprunner_callback(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile to use")
):
    """App Runner deployment management."""
    handle_profile_param(profile)


@app.command("create")
def create_service(
    name: str = typer.Argument(..., help="Service name"),
    image: str = typer.Option(..., "--image", "-i", help="ECR image URI"),
    port: int = typer.Option(8080, "--port", "-p", help="Container port"),
    cpu: int = typer.Option(1024, "--cpu", help="CPU units (256, 512, 1024, 2048, 4096)"),
    memory: int = typer.Option(2048, "--memory", help="Memory in MB"),
    role_arn: str = typer.Option(..., "--role", "-r", help="IAM role ARN for ECR access"),
    auto_deploy: bool = typer.Option(True, "--auto-deploy/--no-auto-deploy", help="Enable auto deployments"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Create a new App Runner service."""
    client = boto3.client("apprunner", region_name=region)

    try:
        response = client.create_service(
            ServiceName=name,
            SourceConfiguration={
                "ImageRepository": {
                    "ImageIdentifier": image,
                    "ImageRepositoryType": "ECR",
                    "ImageConfiguration": {
                        "Port": str(port)
                    }
                },
                "AuthenticationConfiguration": {
                    "AccessRoleArn": role_arn
                },
                "AutoDeploymentsEnabled": auto_deploy
            },
            InstanceConfiguration={
                "Cpu": str(cpu),
                "Memory": str(memory)
            }
        )

        console.print(f"[green]App Runner service '{name}' is being created.[/green]")
        console.print(f"Service ARN: {response['Service']['ServiceArn']}")
        console.print(f"Status: {response['Service']['Status']}")

    except Exception as e:
        console.print(f"[red]Failed to create App Runner service: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_services(
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """List all App Runner services."""
    client = boto3.client("apprunner", region_name=region)

    try:
        response = client.list_services()

        table = Table(title="App Runner Services")
        table.add_column("Name", style="cyan")
        table.add_column("ARN", style="dim")
        table.add_column("Status", style="green")
        table.add_column("URL", style="blue")

        for service in response.get("ServiceSummaryList", []):
            table.add_row(
                service["ServiceName"],
                service["ServiceArn"],
                service["Status"],
                service.get("ServiceUrl", "N/A")
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list services: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_service(
    service_arn: str = typer.Argument(..., help="Service ARN to delete"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Delete an App Runner service."""
    client = boto3.client("apprunner", region_name=region)

    try:
        response = client.delete_service(ServiceArn=service_arn)
        console.print(f"[green]Service deletion initiated: {response['Service']['Status']}[/green]")

    except Exception as e:
        console.print(f"[red]Failed to delete service: {e}[/red]")
        raise typer.Exit(1)


@app.command("deploy")
def deploy_service(
    service_arn: str = typer.Argument(..., help="Service ARN to deploy"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Trigger a new deployment for an App Runner service."""
    client = boto3.client("apprunner", region_name=region)

    try:
        response = client.start_deployment(ServiceArn=service_arn)
        console.print(f"[green]Deployment started: {response['OperationId']}[/green]")

    except Exception as e:
        console.print(f"[red]Failed to start deployment: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
def service_status(
    service_arn: str = typer.Argument(..., help="Service ARN"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Get status of an App Runner service."""
    client = boto3.client("apprunner", region_name=region)

    try:
        response = client.describe_service(ServiceArn=service_arn)
        service = response["Service"]

        console.print(f"[bold]Service: {service['ServiceName']}[/bold]")
        console.print(f"Status: {service['Status']}")
        console.print(f"URL: https://{service.get('ServiceUrl', 'N/A')}")
        console.print(f"Created: {service['CreatedAt']}")
        console.print(f"Updated: {service['UpdatedAt']}")

    except Exception as e:
        console.print(f"[red]Failed to get service status: {e}[/red]")
        raise typer.Exit(1)
