"""ECR repository management commands."""

import typer
import boto3
import base64
from typing import Optional
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("create")
def create_repository(
    name: str = typer.Argument(..., help="Repository name"),
    scan_on_push: bool = typer.Option(True, "--scan/--no-scan", help="Enable image scanning on push"),
    immutable: bool = typer.Option(False, "--immutable/--mutable", help="Enable tag immutability"),
    encryption: str = typer.Option("AES256", "--encryption", help="Encryption type (AES256, KMS)"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Create a new ECR repository."""
    client = boto3.client("ecr", region_name=region)

    try:
        response = client.create_repository(
            repositoryName=name,
            imageScanningConfiguration={
                "scanOnPush": scan_on_push
            },
            imageTagMutability="IMMUTABLE" if immutable else "MUTABLE",
            encryptionConfiguration={
                "encryptionType": encryption
            }
        )

        repo = response["repository"]
        console.print(f"[green]ECR repository '{name}' created successfully![/green]")
        console.print(f"Repository URI: {repo['repositoryUri']}")
        console.print(f"Registry ID: {repo['registryId']}")

    except client.exceptions.RepositoryAlreadyExistsException:
        console.print(f"[yellow]Repository '{name}' already exists.[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to create repository: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_repositories(
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """List all ECR repositories."""
    client = boto3.client("ecr", region_name=region)

    try:
        response = client.describe_repositories()

        table = Table(title="ECR Repositories")
        table.add_column("Name", style="cyan")
        table.add_column("URI", style="blue")
        table.add_column("Created", style="dim")
        table.add_column("Scan on Push", style="green")

        for repo in response.get("repositories", []):
            table.add_row(
                repo["repositoryName"],
                repo["repositoryUri"],
                str(repo["createdAt"]),
                str(repo.get("imageScanningConfiguration", {}).get("scanOnPush", False))
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list repositories: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_repository(
    name: str = typer.Argument(..., help="Repository name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Force delete even if images exist"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Delete an ECR repository."""
    client = boto3.client("ecr", region_name=region)

    try:
        client.delete_repository(
            repositoryName=name,
            force=force
        )
        console.print(f"[green]Repository '{name}' deleted successfully![/green]")

    except Exception as e:
        console.print(f"[red]Failed to delete repository: {e}[/red]")
        raise typer.Exit(1)


@app.command("login")
def docker_login(
    region: str = typer.Option(None, "--region", help="AWS region"),
    execute: bool = typer.Option(False, "--execute", "-e", help="Execute docker login directly")
):
    """Get Docker login command for ECR."""
    client = boto3.client("ecr", region_name=region)
    sts = boto3.client("sts")

    try:
        account_id = sts.get_caller_identity()["Account"]
        response = client.get_authorization_token()

        auth_data = response["authorizationData"][0]
        token = base64.b64decode(auth_data["authorizationToken"]).decode()
        username, password = token.split(":")
        registry = f"{account_id}.dkr.ecr.{region}.amazonaws.com"

        if execute:
            # Execute docker login directly
            import subprocess
            login_cmd = f"docker login --username AWS --password {password} {registry}"
            result = subprocess.run(login_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                console.print(f"[green]Successfully logged in to {registry}[/green]")
            else:
                console.print(f"[red]Login failed: {result.stderr}[/red]")
                raise typer.Exit(1)
        else:
            # Print the command for user to run
            console.print("[bold]Run this command to login:[/bold]")
            console.print(f"docker login -u AWS -p {password} {registry}")

    except Exception as e:
        console.print(f"[red]Failed to get login token: {e}[/red]")
        raise typer.Exit(1)


@app.command("images")
def list_images(
    name: str = typer.Argument(..., help="Repository name"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """List images in an ECR repository."""
    client = boto3.client("ecr", region_name=region)

    try:
        response = client.describe_images(repositoryName=name)

        table = Table(title=f"Images in {name}")
        table.add_column("Tag", style="cyan")
        table.add_column("Digest", style="dim")
        table.add_column("Size (MB)", style="green")
        table.add_column("Pushed", style="blue")

        for image in response.get("imageDetails", []):
            tags = ", ".join(image.get("imageTags", ["<untagged>"]))
            size_mb = round(image.get("imageSizeInBytes", 0) / 1024 / 1024, 2)

            table.add_row(
                tags,
                image["imageDigest"][:20] + "...",
                str(size_mb),
                str(image["imagePushedAt"])
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list images: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete-image")
def delete_image(
    name: str = typer.Argument(..., help="Repository name"),
    tag: str = typer.Option(None, "--tag", "-t", help="Image tag to delete"),
    digest: str = typer.Option(None, "--digest", "-d", help="Image digest to delete"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Delete an image from ECR repository."""
    if not tag and not digest:
        console.print("[red]Either --tag or --digest must be specified[/red]")
        raise typer.Exit(1)

    client = boto3.client("ecr", region_name=region)

    try:
        image_id = {}
        if tag:
            image_id["imageTag"] = tag
        if digest:
            image_id["imageDigest"] = digest

        client.batch_delete_image(
            repositoryName=name,
            imageIds=[image_id]
        )
        console.print(f"[green]Image deleted successfully![/green]")

    except Exception as e:
        console.print(f"[red]Failed to delete image: {e}[/red]")
        raise typer.Exit(1)
