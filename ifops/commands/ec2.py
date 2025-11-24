"""EC2 instance management commands."""

import typer
import boto3
from typing import Optional, List
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("create")
def create_instance(
    name: str = typer.Argument(..., help="Instance name tag"),
    ami: str = typer.Option(..., "--ami", "-a", help="AMI ID"),
    instance_type: str = typer.Option("t3.micro", "--type", "-t", help="Instance type"),
    key_name: str = typer.Option(None, "--key", "-k", help="Key pair name"),
    security_groups: str = typer.Option(None, "--sg", help="Security group IDs (comma-separated)"),
    subnet: str = typer.Option(None, "--subnet", "-s", help="Subnet ID"),
    user_data: str = typer.Option(None, "--user-data", help="Path to user data script"),
    volume_size: int = typer.Option(8, "--volume-size", help="Root volume size in GB"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Create a new EC2 instance."""
    client = boto3.client("ec2", region_name=region)

    try:
        params = {
            "ImageId": ami,
            "InstanceType": instance_type,
            "MinCount": 1,
            "MaxCount": 1,
            "TagSpecifications": [
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": name}]
                }
            ],
            "BlockDeviceMappings": [
                {
                    "DeviceName": "/dev/xvda",
                    "Ebs": {
                        "VolumeSize": volume_size,
                        "VolumeType": "gp3",
                        "DeleteOnTermination": True
                    }
                }
            ]
        }

        if key_name:
            params["KeyName"] = key_name

        if security_groups:
            params["SecurityGroupIds"] = security_groups.split(",")

        if subnet:
            params["SubnetId"] = subnet

        if user_data:
            with open(user_data, "r") as f:
                params["UserData"] = f.read()

        response = client.run_instances(**params)
        instance = response["Instances"][0]

        console.print(f"[green]EC2 instance '{name}' created successfully![/green]")
        console.print(f"Instance ID: {instance['InstanceId']}")
        console.print(f"State: {instance['State']['Name']}")

    except Exception as e:
        console.print(f"[red]Failed to create instance: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_instances(
    state: str = typer.Option(None, "--state", help="Filter by state (running, stopped, etc)"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """List EC2 instances."""
    client = boto3.client("ec2", region_name=region)

    try:
        filters = []
        if state:
            filters.append({"Name": "instance-state-name", "Values": [state]})

        response = client.describe_instances(Filters=filters if filters else [])

        table = Table(title="EC2 Instances")
        table.add_column("Name", style="cyan")
        table.add_column("Instance ID", style="dim")
        table.add_column("Type", style="blue")
        table.add_column("State", style="green")
        table.add_column("Public IP", style="yellow")
        table.add_column("Private IP", style="dim")

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                name = "N/A"
                for tag in instance.get("Tags", []):
                    if tag["Key"] == "Name":
                        name = tag["Value"]
                        break

                table.add_row(
                    name,
                    instance["InstanceId"],
                    instance["InstanceType"],
                    instance["State"]["Name"],
                    instance.get("PublicIpAddress", "N/A"),
                    instance.get("PrivateIpAddress", "N/A")
                )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list instances: {e}[/red]")
        raise typer.Exit(1)


@app.command("start")
def start_instance(
    instance_ids: str = typer.Argument(..., help="Instance IDs (comma-separated)"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Start EC2 instances."""
    client = boto3.client("ec2", region_name=region)

    try:
        ids = instance_ids.split(",")
        response = client.start_instances(InstanceIds=ids)

        for instance in response.get("StartingInstances", []):
            console.print(f"[green]Instance {instance['InstanceId']}: {instance['PreviousState']['Name']} -> {instance['CurrentState']['Name']}[/green]")

    except Exception as e:
        console.print(f"[red]Failed to start instances: {e}[/red]")
        raise typer.Exit(1)


@app.command("stop")
def stop_instance(
    instance_ids: str = typer.Argument(..., help="Instance IDs (comma-separated)"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Stop EC2 instances."""
    client = boto3.client("ec2", region_name=region)

    try:
        ids = instance_ids.split(",")
        response = client.stop_instances(InstanceIds=ids)

        for instance in response.get("StoppingInstances", []):
            console.print(f"[green]Instance {instance['InstanceId']}: {instance['PreviousState']['Name']} -> {instance['CurrentState']['Name']}[/green]")

    except Exception as e:
        console.print(f"[red]Failed to stop instances: {e}[/red]")
        raise typer.Exit(1)


@app.command("terminate")
def terminate_instance(
    instance_ids: str = typer.Argument(..., help="Instance IDs (comma-separated)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Terminate EC2 instances."""
    if not force:
        confirm = typer.confirm(f"Are you sure you want to terminate instances: {instance_ids}?")
        if not confirm:
            raise typer.Abort()

    client = boto3.client("ec2", region_name=region)

    try:
        ids = instance_ids.split(",")
        response = client.terminate_instances(InstanceIds=ids)

        for instance in response.get("TerminatingInstances", []):
            console.print(f"[green]Instance {instance['InstanceId']}: {instance['CurrentState']['Name']}[/green]")

    except Exception as e:
        console.print(f"[red]Failed to terminate instances: {e}[/red]")
        raise typer.Exit(1)


@app.command("modify")
def modify_instance(
    instance_id: str = typer.Argument(..., help="Instance ID"),
    instance_type: str = typer.Option(None, "--type", "-t", help="New instance type"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Modify EC2 instance attributes (instance must be stopped)."""
    client = boto3.client("ec2", region_name=region)

    try:
        if instance_type:
            client.modify_instance_attribute(
                InstanceId=instance_id,
                InstanceType={"Value": instance_type}
            )
            console.print(f"[green]Instance type changed to {instance_type}[/green]")

    except Exception as e:
        console.print(f"[red]Failed to modify instance: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
def instance_status(
    instance_id: str = typer.Argument(..., help="Instance ID"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Get detailed status of an EC2 instance."""
    client = boto3.client("ec2", region_name=region)

    try:
        response = client.describe_instances(InstanceIds=[instance_id])

        if not response["Reservations"]:
            console.print(f"[red]Instance {instance_id} not found[/red]")
            raise typer.Exit(1)

        instance = response["Reservations"][0]["Instances"][0]

        name = "N/A"
        for tag in instance.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
                break

        console.print(f"[bold]Instance: {name} ({instance_id})[/bold]")
        console.print(f"State: {instance['State']['Name']}")
        console.print(f"Type: {instance['InstanceType']}")
        console.print(f"AMI: {instance['ImageId']}")
        console.print(f"Public IP: {instance.get('PublicIpAddress', 'N/A')}")
        console.print(f"Private IP: {instance.get('PrivateIpAddress', 'N/A')}")
        console.print(f"VPC: {instance.get('VpcId', 'N/A')}")
        console.print(f"Subnet: {instance.get('SubnetId', 'N/A')}")
        console.print(f"Launch Time: {instance['LaunchTime']}")

    except Exception as e:
        console.print(f"[red]Failed to get instance status: {e}[/red]")
        raise typer.Exit(1)
