"""Project-based declarative infrastructure management."""

import typer
import boto3
import json
import yaml
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.table import Table

from ifops.core.config import get_config_dir, handle_profile_param

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.callback()
def project_callback(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile to use")
):
    """Declarative infrastructure projects (like Terraform)."""
    handle_profile_param(profile)

# Projects directory
PROJECTS_DIR = get_config_dir() / "projects"


def get_project_dir(name: str) -> Path:
    """Get project directory path."""
    return PROJECTS_DIR / name


def load_project_state(name: str) -> dict:
    """Load project state."""
    project_dir = get_project_dir(name)
    state_file = project_dir / "state.json"

    if not state_file.exists():
        return {"resources": [], "created_at": None, "updated_at": None}

    with open(state_file, "r") as f:
        return json.load(f)


def load_project_config(name: str) -> dict:
    """Load project infrastructure configuration from stored config_path."""
    state = load_project_state(name)
    config_path = state.get("config_path")

    # Try 1: Original stored path
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "r") as f:
                return yaml.safe_load(f) or {}

    # Try 2: Current directory fallback
    cwd_config = Path.cwd() / "infra.yaml"
    if cwd_config.exists():
        # Update state with new config path
        state["config_path"] = str(cwd_config)
        save_project_state(name, state)

        with open(cwd_config, "r") as f:
            return yaml.safe_load(f) or {}

    # Config not found - show helpful error
    console.print(f"[red]✗ Cannot find infra.yaml for project '{name}'[/red]")
    console.print(f"[yellow]Tried:[/yellow]")
    if config_path:
        console.print(f"  1. {config_path} (original)")
    console.print(f"  2. {cwd_config} (current directory)")
    console.print(f"\n[yellow]Solutions:[/yellow]")
    console.print(f"  • Run this command from the directory containing infra.yaml")
    console.print(f"  • Or create a new infra.yaml: [cyan]ifops project create {name}[/cyan]")
    import typer
    raise typer.Exit(1)


def save_project_state(name: str, state: dict) -> None:
    """Save project state."""
    project_dir = get_project_dir(name)
    state_file = project_dir / "state.json"

    state["updated_at"] = datetime.now().isoformat()

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


@app.command("create")
def create_project(
    name: str = typer.Argument(..., help="Project name"),
    description: str = typer.Option("", "--description", "-d", help="Project description"),
    region: str = typer.Option("us-east-1", "--region", "-r", help="AWS region for resources")
):
    """Create a new infrastructure project in current directory."""
    # Create infra.yaml in current working directory
    cwd = Path.cwd()
    config_file = cwd / "infra.yaml"

    if config_file.exists():
        console.print(f"[red]infra.yaml already exists in current directory[/red]")
        raise typer.Exit(1)

    # Create state directory in ~/.ifops/projects/
    project_dir = get_project_dir(name)
    if project_dir.exists():
        console.print(f"[red]Project '{name}' already exists in ~/.ifops/projects/[/red]")
        raise typer.Exit(1)

    project_dir.mkdir(parents=True)

    # Create default infra.yaml in current directory
    default_config = {
        "name": name,
        "description": description,
        "region": region,
        "resources": [
            {
                "type": "ecr",
                "name": f"{name}-repo",
                "scan_on_push": True,
                "_comment": "Example ECR repository - modify or remove"
            }
        ]
    }

    with open(config_file, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

    # Create empty state in ~/.ifops/projects/<name>/
    state = {
        "resources": [],
        "config_path": str(config_file),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    save_project_state(name, state)

    console.print(f"[green]✓ Project '{name}' created[/green]")
    console.print(f"  Config: {config_file}")
    console.print(f"  State: {project_dir / 'state.json'}")
    console.print(f"\nEdit infra.yaml to define your infrastructure:")
    console.print(f"  [cyan]nano infra.yaml[/cyan]")
    console.print(f"\nSee available resources:")
    console.print(f"  [cyan]ifops project resources[/cyan]")
    console.print(f"\nThen plan and apply:")
    console.print(f"  [cyan]ifops project plan {name}[/cyan]")
    console.print(f"  [cyan]ifops project apply {name}[/cyan]")


@app.command("resources")
def show_resources():
    """Show available resource types and their properties."""
    console.print("[bold]Available Resource Types for infra.yaml[/bold]\n")

    # ECR
    console.print("[cyan]1. ECR Repository[/cyan]")
    console.print("   type: ecr")
    console.print("   Properties:")
    console.print("     - name: (required) Repository name")
    console.print("     - scan_on_push: (optional) Enable image scanning [default: true]")
    console.print("     - immutable: (optional) Enable tag immutability [default: false]")
    console.print("")

    # S3
    console.print("[cyan]2. S3 Bucket[/cyan]")
    console.print("   type: s3")
    console.print("   Properties:")
    console.print("     - name: (required) Bucket name (must be globally unique)")
    console.print("     - versioning: (optional) Enable versioning [default: false]")
    console.print("     - static_site: (optional) Enable static website hosting [default: false]")
    console.print("")

    # EC2
    console.print("[cyan]3. EC2 Instance[/cyan]")
    console.print("   type: ec2")
    console.print("   Properties:")
    console.print("     - name: (required) Instance name tag")
    console.print("     - ami: (required) AMI ID")
    console.print("     - instance_type: (optional) Instance type [default: t3.micro]")
    console.print("     - key_name: (optional) SSH key pair name")
    console.print("     - security_groups: (optional) List of security group IDs")
    console.print("     - subnet_id: (optional) Subnet ID")
    console.print("")

    # ECS Cluster
    console.print("[cyan]4. ECS Cluster[/cyan]")
    console.print("   type: ecs-cluster")
    console.print("   Properties:")
    console.print("     - name: (required) Cluster name")
    console.print("     - capacity_providers: (optional) List [default: FARGATE, FARGATE_SPOT]")
    console.print("")

    console.print("[bold]Example infra.yaml:[/bold]")
    console.print("""
[dim]name: my-project
description: My web application
region: eu-west-3
resources:
  - type: ecr
    name: my-app-repo
    scan_on_push: true

  - type: s3
    name: my-app-assets
    versioning: true

  - type: ec2
    name: my-app-server
    ami: ami-0123456789abcdef0
    instance_type: t3.small
    key_name: my-key[/dim]
""")


@app.command("list")
def list_projects():
    """List all infrastructure projects."""
    if not PROJECTS_DIR.exists():
        console.print("[yellow]No projects found[/yellow]")
        return

    projects = [d.name for d in PROJECTS_DIR.iterdir() if d.is_dir()]

    if not projects:
        console.print("[yellow]No projects found[/yellow]")
        return

    table = Table(title="Infrastructure Projects")
    table.add_column("Name", style="cyan")
    table.add_column("Resources", style="green")
    table.add_column("Region", style="blue")
    table.add_column("Updated", style="dim")

    for project in sorted(projects):
        config = load_project_config(project)
        state = load_project_state(project)

        resource_count = len(state.get("resources", []))
        region = config.get("region", "N/A")
        updated = state.get("updated_at", "N/A")
        if updated and updated != "N/A":
            updated = updated[:19]  # Trim microseconds

        table.add_row(project, str(resource_count), region, updated)

    console.print(table)


@app.command("show")
def show_project(
    name: str = typer.Argument(..., help="Project name")
):
    """Show project configuration and state."""
    project_dir = get_project_dir(name)

    if not project_dir.exists():
        console.print(f"[red]Project '{name}' not found[/red]")
        raise typer.Exit(1)

    config = load_project_config(name)
    state = load_project_state(name)

    config_path = state.get("config_path", "N/A")

    console.print(f"[bold]Project: {name}[/bold]")
    console.print(f"Description: {config.get('description', 'N/A')}")
    console.print(f"Region: {config.get('region', 'N/A')}")
    console.print(f"Config file: {config_path}")
    console.print(f"State file: {project_dir / 'state.json'}")

    # Show defined resources
    console.print(f"\n[bold]Defined Resources ({len(config.get('resources', []))}):[/bold]")
    for res in config.get("resources", []):
        console.print(f"  - [{res['type']}] {res['name']}")

    # Show deployed resources
    console.print(f"\n[bold]Deployed Resources ({len(state.get('resources', []))}):[/bold]")
    for res in state.get("resources", []):
        console.print(f"  - [{res['type']}] {res['name']}: {res.get('id', 'N/A')}")


@app.command("plan")
def plan_project(
    name: str = typer.Argument(..., help="Project name")
):
    """Show planned changes for a project."""
    project_dir = get_project_dir(name)

    if not project_dir.exists():
        console.print(f"[red]Project '{name}' not found[/red]")
        raise typer.Exit(1)

    config = load_project_config(name)
    state = load_project_state(name)

    defined = {f"{r['type']}:{r['name']}": r for r in config.get("resources", [])}
    deployed = {f"{r['type']}:{r['name']}": r for r in state.get("resources", [])}

    to_create = []
    to_destroy = []
    unchanged = []

    # Find resources to create
    for key, res in defined.items():
        if key not in deployed:
            to_create.append(res)
        else:
            unchanged.append(res)

    # Find resources to destroy
    for key, res in deployed.items():
        if key not in defined:
            to_destroy.append(res)

    console.print(f"[bold]Plan for project: {name}[/bold]")
    console.print(f"Region: {config.get('region', 'us-east-1')}\n")

    if to_create:
        console.print(f"[green]+ Create ({len(to_create)}):[/green]")
        for res in to_create:
            console.print(f"  + [{res['type']}] {res['name']}")

    if to_destroy:
        console.print(f"\n[red]- Destroy ({len(to_destroy)}):[/red]")
        for res in to_destroy:
            console.print(f"  - [{res['type']}] {res['name']}")

    if unchanged:
        console.print(f"\n[dim]= Unchanged ({len(unchanged)}):[/dim]")
        for res in unchanged:
            console.print(f"  = [{res['type']}] {res['name']}")

    if not to_create and not to_destroy:
        console.print("[green]No changes required[/green]")
    else:
        console.print(f"\nTo apply these changes, run:")
        console.print(f"  [cyan]ifops project apply {name}[/cyan]")


@app.command("apply")
def apply_project(
    name: str = typer.Argument(..., help="Project name"),
    auto_approve: bool = typer.Option(False, "--auto-approve", "-y", help="Skip confirmation")
):
    """Apply infrastructure changes for a project."""
    project_dir = get_project_dir(name)

    if not project_dir.exists():
        console.print(f"[red]Project '{name}' not found[/red]")
        raise typer.Exit(1)

    config = load_project_config(name)
    state = load_project_state(name)
    region = config.get("region", "us-east-1")

    defined = {f"{r['type']}:{r['name']}": r for r in config.get("resources", [])}
    deployed = {f"{r['type']}:{r['name']}": r for r in state.get("resources", [])}

    to_create = []
    to_destroy = []

    for key, res in defined.items():
        if key not in deployed:
            to_create.append(res)

    for key, res in deployed.items():
        if key not in defined:
            to_destroy.append(res)

    if not to_create and not to_destroy:
        console.print("[green]No changes to apply[/green]")
        return

    # Show plan
    console.print(f"[bold]Applying changes to: {name}[/bold]\n")

    if to_create:
        console.print(f"[green]+ Will create {len(to_create)} resource(s)[/green]")
    if to_destroy:
        console.print(f"[red]- Will destroy {len(to_destroy)} resource(s)[/red]")

    if not auto_approve:
        confirm = typer.confirm("\nDo you want to apply these changes?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    # Apply changes
    new_resources = list(state.get("resources", []))

    # Create resources
    for res in to_create:
        console.print(f"\n[yellow]Creating [{res['type']}] {res['name']}...[/yellow]")
        try:
            resource_id = _create_resource(res, region)
            new_resources.append({
                "type": res["type"],
                "name": res["name"],
                "id": resource_id,
                "created_at": datetime.now().isoformat()
            })
            console.print(f"[green]✓ Created: {resource_id}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to create: {e}[/red]")

    # Destroy resources
    for res in to_destroy:
        console.print(f"\n[yellow]Destroying [{res['type']}] {res['name']}...[/yellow]")
        try:
            _destroy_resource(res, region)
            new_resources = [r for r in new_resources if not (r["type"] == res["type"] and r["name"] == res["name"])]
            console.print(f"[green]✓ Destroyed[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to destroy: {e}[/red]")

    # Save state
    state["resources"] = new_resources
    save_project_state(name, state)

    console.print(f"\n[green]Apply complete![/green]")


@app.command("destroy")
def destroy_project(
    name: str = typer.Argument(..., help="Project name"),
    auto_approve: bool = typer.Option(False, "--auto-approve", "-y", help="Skip confirmation")
):
    """Destroy all resources in a project."""
    project_dir = get_project_dir(name)

    if not project_dir.exists():
        console.print(f"[red]Project '{name}' not found[/red]")
        raise typer.Exit(1)

    config = load_project_config(name)
    state = load_project_state(name)
    region = config.get("region", "us-east-1")

    resources = state.get("resources", [])

    if not resources:
        console.print("[yellow]No resources to destroy[/yellow]")
        return

    console.print(f"[bold red]Destroying all resources in: {name}[/bold red]\n")

    for res in resources:
        console.print(f"  - [{res['type']}] {res['name']}")

    if not auto_approve:
        confirm = typer.confirm(f"\nAre you sure you want to destroy {len(resources)} resource(s)?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    # Destroy resources
    for res in resources:
        console.print(f"\n[yellow]Destroying [{res['type']}] {res['name']}...[/yellow]")
        try:
            _destroy_resource(res, region)
            console.print(f"[green]✓ Destroyed[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed: {e}[/red]")

    # Clear state
    state["resources"] = []
    save_project_state(name, state)

    console.print(f"\n[green]All resources destroyed![/green]")


@app.command("delete")
def delete_project(
    name: str = typer.Argument(..., help="Project name"),
    force: bool = typer.Option(False, "--force", "-f", help="Delete even if resources exist")
):
    """Delete a project (config and state files)."""
    project_dir = get_project_dir(name)

    if not project_dir.exists():
        console.print(f"[red]Project '{name}' not found[/red]")
        raise typer.Exit(1)

    state = load_project_state(name)

    if state.get("resources") and not force:
        console.print(f"[red]Project has {len(state['resources'])} deployed resources[/red]")
        console.print(f"Run 'ifops project destroy {name}' first, or use --force")
        raise typer.Exit(1)

    import shutil
    shutil.rmtree(project_dir)

    console.print(f"[green]✓ Project '{name}' deleted[/green]")


def _create_resource(resource: dict, region: str) -> str:
    """Create a resource and return its ID."""
    res_type = resource["type"]
    name = resource["name"]

    if res_type == "ecr":
        client = boto3.client("ecr", region_name=region)
        response = client.create_repository(
            repositoryName=name,
            imageScanningConfiguration={
                "scanOnPush": resource.get("scan_on_push", True)
            }
        )
        return response["repository"]["repositoryUri"]

    elif res_type == "s3":
        client = boto3.client("s3", region_name=region)
        if region == "us-east-1":
            client.create_bucket(Bucket=name)
        else:
            client.create_bucket(
                Bucket=name,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
        return f"s3://{name}"

    elif res_type == "ec2":
        client = boto3.client("ec2", region_name=region)
        response = client.run_instances(
            ImageId=resource["ami"],
            InstanceType=resource.get("instance_type", "t3.micro"),
            MinCount=1,
            MaxCount=1,
            KeyName=resource.get("key_name"),
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": name}]
            }]
        )
        return response["Instances"][0]["InstanceId"]

    else:
        raise ValueError(f"Unknown resource type: {res_type}")


def _destroy_resource(resource: dict, region: str) -> None:
    """Destroy a resource."""
    res_type = resource["type"]
    name = resource["name"]
    res_id = resource.get("id", "")

    if res_type == "ecr":
        client = boto3.client("ecr", region_name=region)
        client.delete_repository(repositoryName=name, force=True)

    elif res_type == "s3":
        s3 = boto3.resource("s3", region_name=region)
        bucket = s3.Bucket(name)
        bucket.objects.all().delete()
        bucket.delete()

    elif res_type == "ec2":
        client = boto3.client("ec2", region_name=region)
        instance_id = res_id if res_id.startswith("i-") else None
        if instance_id:
            client.terminate_instances(InstanceIds=[instance_id])

    else:
        raise ValueError(f"Unknown resource type: {res_type}")
