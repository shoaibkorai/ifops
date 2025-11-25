"""ECS cluster, task, and service management commands."""

import typer
import boto3
import json
from typing import Optional
from rich.console import Console
from rich.table import Table

from ifops.core.config import handle_profile_param

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.callback()
def ecs_callback(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile to use")
):
    """ECS cluster/task/service management."""
    handle_profile_param(profile)


# Cluster commands
@app.command("create-cluster")
def create_cluster(
    name: str = typer.Argument(..., help="Cluster name"),
    capacity_providers: str = typer.Option("FARGATE,FARGATE_SPOT", "--capacity-providers", help="Capacity providers (comma-separated)"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Create a new ECS cluster."""
    client = boto3.client("ecs", region_name=region)

    try:
        providers = capacity_providers.split(",")
        response = client.create_cluster(
            clusterName=name,
            capacityProviders=providers,
            defaultCapacityProviderStrategy=[
                {"capacityProvider": providers[0], "weight": 1}
            ],
            settings=[
                {"name": "containerInsights", "value": "enabled"}
            ]
        )

        cluster = response["cluster"]
        console.print(f"[green]ECS cluster '{name}' created successfully![/green]")
        console.print(f"Cluster ARN: {cluster['clusterArn']}")
        console.print(f"Status: {cluster['status']}")

    except Exception as e:
        console.print(f"[red]Failed to create cluster: {e}[/red]")
        raise typer.Exit(1)


@app.command("list-clusters")
def list_clusters(
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """List all ECS clusters."""
    client = boto3.client("ecs", region_name=region)

    try:
        response = client.list_clusters()

        if not response.get("clusterArns"):
            console.print("[yellow]No clusters found[/yellow]")
            return

        clusters = client.describe_clusters(clusters=response["clusterArns"])

        table = Table(title="ECS Clusters")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Running Tasks", style="blue")
        table.add_column("Services", style="yellow")

        for cluster in clusters.get("clusters", []):
            table.add_row(
                cluster["clusterName"],
                cluster["status"],
                str(cluster["runningTasksCount"]),
                str(cluster["activeServicesCount"])
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list clusters: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete-cluster")
def delete_cluster(
    name: str = typer.Argument(..., help="Cluster name to delete"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Delete an ECS cluster."""
    client = boto3.client("ecs", region_name=region)

    try:
        client.delete_cluster(cluster=name)
        console.print(f"[green]Cluster '{name}' deleted successfully![/green]")

    except Exception as e:
        console.print(f"[red]Failed to delete cluster: {e}[/red]")
        raise typer.Exit(1)


# Task Definition commands
@app.command("register-task")
def register_task_definition(
    family: str = typer.Argument(..., help="Task definition family name"),
    container_name: str = typer.Option(..., "--container", "-c", help="Container name"),
    image: str = typer.Option(..., "--image", "-i", help="Container image"),
    cpu: str = typer.Option("256", "--cpu", help="Task CPU units"),
    memory: str = typer.Option("512", "--memory", help="Task memory in MB"),
    port: int = typer.Option(None, "--port", "-p", help="Container port"),
    execution_role: str = typer.Option(..., "--execution-role", help="Task execution role ARN"),
    task_role: str = typer.Option(None, "--task-role", help="Task role ARN"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Register a new task definition."""
    client = boto3.client("ecs", region_name=region)

    try:
        container_def = {
            "name": container_name,
            "image": image,
            "essential": True,
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": f"/ecs/{family}",
                    "awslogs-region": region,
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }

        if port:
            container_def["portMappings"] = [
                {
                    "containerPort": port,
                    "protocol": "tcp"
                }
            ]

        params = {
            "family": family,
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": cpu,
            "memory": memory,
            "executionRoleArn": execution_role,
            "containerDefinitions": [container_def]
        }

        if task_role:
            params["taskRoleArn"] = task_role

        response = client.register_task_definition(**params)
        task_def = response["taskDefinition"]

        console.print(f"[green]Task definition registered successfully![/green]")
        console.print(f"Task Definition ARN: {task_def['taskDefinitionArn']}")
        console.print(f"Revision: {task_def['revision']}")

    except Exception as e:
        console.print(f"[red]Failed to register task definition: {e}[/red]")
        raise typer.Exit(1)


@app.command("list-tasks")
def list_task_definitions(
    family: str = typer.Option(None, "--family", "-f", help="Filter by family name"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """List task definitions."""
    client = boto3.client("ecs", region_name=region)

    try:
        params = {"status": "ACTIVE"}
        if family:
            params["familyPrefix"] = family

        response = client.list_task_definitions(**params)

        table = Table(title="Task Definitions")
        table.add_column("Task Definition ARN", style="cyan")

        for arn in response.get("taskDefinitionArns", []):
            table.add_row(arn)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list task definitions: {e}[/red]")
        raise typer.Exit(1)


# Service commands
@app.command("create-service")
def create_service(
    cluster: str = typer.Argument(..., help="Cluster name"),
    name: str = typer.Option(..., "--name", "-n", help="Service name"),
    task_definition: str = typer.Option(..., "--task-def", "-t", help="Task definition ARN or family:revision"),
    desired_count: int = typer.Option(1, "--count", "-c", help="Desired task count"),
    subnets: str = typer.Option(..., "--subnets", help="Subnet IDs (comma-separated)"),
    security_groups: str = typer.Option(..., "--sg", help="Security group IDs (comma-separated)"),
    assign_public_ip: bool = typer.Option(True, "--public-ip/--no-public-ip", help="Assign public IP"),
    target_group_arn: str = typer.Option(None, "--target-group", help="Target group ARN for load balancer"),
    container_name: str = typer.Option(None, "--container", help="Container name for load balancer"),
    container_port: int = typer.Option(None, "--port", help="Container port for load balancer"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Create a new ECS service."""
    client = boto3.client("ecs", region_name=region)

    try:
        params = {
            "cluster": cluster,
            "serviceName": name,
            "taskDefinition": task_definition,
            "desiredCount": desired_count,
            "launchType": "FARGATE",
            "networkConfiguration": {
                "awsvpcConfiguration": {
                    "subnets": subnets.split(","),
                    "securityGroups": security_groups.split(","),
                    "assignPublicIp": "ENABLED" if assign_public_ip else "DISABLED"
                }
            }
        }

        if target_group_arn and container_name and container_port:
            params["loadBalancers"] = [
                {
                    "targetGroupArn": target_group_arn,
                    "containerName": container_name,
                    "containerPort": container_port
                }
            ]

        response = client.create_service(**params)
        service = response["service"]

        console.print(f"[green]ECS service '{name}' created successfully![/green]")
        console.print(f"Service ARN: {service['serviceArn']}")
        console.print(f"Status: {service['status']}")

    except Exception as e:
        console.print(f"[red]Failed to create service: {e}[/red]")
        raise typer.Exit(1)


@app.command("list-services")
def list_services(
    cluster: str = typer.Argument(..., help="Cluster name"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """List services in a cluster."""
    client = boto3.client("ecs", region_name=region)

    try:
        response = client.list_services(cluster=cluster)

        if not response.get("serviceArns"):
            console.print("[yellow]No services found[/yellow]")
            return

        services = client.describe_services(
            cluster=cluster,
            services=response["serviceArns"]
        )

        table = Table(title=f"Services in {cluster}")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Desired", style="blue")
        table.add_column("Running", style="yellow")
        table.add_column("Task Definition", style="dim")

        for service in services.get("services", []):
            table.add_row(
                service["serviceName"],
                service["status"],
                str(service["desiredCount"]),
                str(service["runningCount"]),
                service["taskDefinition"].split("/")[-1]
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list services: {e}[/red]")
        raise typer.Exit(1)


@app.command("update-service")
def update_service(
    cluster: str = typer.Argument(..., help="Cluster name"),
    service: str = typer.Option(..., "--service", "-s", help="Service name"),
    task_definition: str = typer.Option(None, "--task-def", "-t", help="New task definition"),
    desired_count: int = typer.Option(None, "--count", "-c", help="New desired count"),
    force: bool = typer.Option(False, "--force", "-f", help="Force new deployment"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Update an ECS service."""
    client = boto3.client("ecs", region_name=region)

    try:
        params = {
            "cluster": cluster,
            "service": service,
            "forceNewDeployment": force
        }

        if task_definition:
            params["taskDefinition"] = task_definition
        if desired_count is not None:
            params["desiredCount"] = desired_count

        response = client.update_service(**params)
        service_info = response["service"]

        console.print(f"[green]Service '{service}' updated successfully![/green]")
        console.print(f"New deployment: {service_info['deployments'][0]['id']}")

    except Exception as e:
        console.print(f"[red]Failed to update service: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete-service")
def delete_service(
    cluster: str = typer.Argument(..., help="Cluster name"),
    service: str = typer.Option(..., "--service", "-s", help="Service name"),
    force: bool = typer.Option(False, "--force", "-f", help="Force delete without draining"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Delete an ECS service."""
    client = boto3.client("ecs", region_name=region)

    try:
        # First scale down to 0
        if not force:
            client.update_service(
                cluster=cluster,
                service=service,
                desiredCount=0
            )
            console.print("[yellow]Scaling down service to 0...[/yellow]")

        client.delete_service(
            cluster=cluster,
            service=service,
            force=force
        )
        console.print(f"[green]Service '{service}' deleted successfully![/green]")

    except Exception as e:
        console.print(f"[red]Failed to delete service: {e}[/red]")
        raise typer.Exit(1)


@app.command("run-task")
def run_task(
    cluster: str = typer.Argument(..., help="Cluster name"),
    task_definition: str = typer.Option(..., "--task-def", "-t", help="Task definition ARN or family:revision"),
    subnets: str = typer.Option(..., "--subnets", help="Subnet IDs (comma-separated)"),
    security_groups: str = typer.Option(..., "--sg", help="Security group IDs (comma-separated)"),
    count: int = typer.Option(1, "--count", "-c", help="Number of tasks to run"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Run a one-off task."""
    client = boto3.client("ecs", region_name=region)

    try:
        response = client.run_task(
            cluster=cluster,
            taskDefinition=task_definition,
            count=count,
            launchType="FARGATE",
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": subnets.split(","),
                    "securityGroups": security_groups.split(","),
                    "assignPublicIp": "ENABLED"
                }
            }
        )

        for task in response.get("tasks", []):
            console.print(f"[green]Task started: {task['taskArn']}[/green]")

        for failure in response.get("failures", []):
            console.print(f"[red]Failed: {failure['reason']}[/red]")

    except Exception as e:
        console.print(f"[red]Failed to run task: {e}[/red]")
        raise typer.Exit(1)
