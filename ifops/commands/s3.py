"""S3 bucket management and static site hosting commands."""

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
def s3_callback(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="AWS profile to use")
):
    """S3 bucket management and static site hosting."""
    handle_profile_param(profile)


@app.command("create")
def create_bucket(
    name: str = typer.Argument(..., help="Bucket name"),
    region: str = typer.Option(None, "--region", help="AWS region"),
    versioning: bool = typer.Option(False, "--versioning/--no-versioning", help="Enable versioning"),
    public: bool = typer.Option(False, "--public/--private", help="Allow public access")
):
    """Create a new S3 bucket."""
    client = boto3.client("s3", region_name=region)

    try:
        # Create bucket
        create_params = {"Bucket": name}
        if region != "us-east-1":
            create_params["CreateBucketConfiguration"] = {
                "LocationConstraint": region
            }

        client.create_bucket(**create_params)
        console.print(f"[green]S3 bucket '{name}' created successfully![/green]")

        # Configure versioning
        if versioning:
            client.put_bucket_versioning(
                Bucket=name,
                VersioningConfiguration={"Status": "Enabled"}
            )
            console.print("[green]Versioning enabled[/green]")

        # Block public access by default
        if not public:
            client.put_public_access_block(
                Bucket=name,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True
                }
            )
            console.print("[green]Public access blocked[/green]")

    except client.exceptions.BucketAlreadyExists:
        console.print(f"[yellow]Bucket '{name}' already exists globally[/yellow]")
    except client.exceptions.BucketAlreadyOwnedByYou:
        console.print(f"[yellow]Bucket '{name}' already owned by you[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to create bucket: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_buckets():
    """List all S3 buckets."""
    client = boto3.client("s3")

    try:
        response = client.list_buckets()

        table = Table(title="S3 Buckets")
        table.add_column("Name", style="cyan")
        table.add_column("Created", style="dim")

        for bucket in response.get("Buckets", []):
            table.add_row(
                bucket["Name"],
                str(bucket["CreationDate"])
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list buckets: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_bucket(
    name: str = typer.Argument(..., help="Bucket name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Delete all objects first"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Delete an S3 bucket."""
    s3 = boto3.resource("s3", region_name=region)
    bucket = s3.Bucket(name)

    try:
        if force:
            console.print("[yellow]Deleting all objects...[/yellow]")
            bucket.objects.all().delete()
            bucket.object_versions.all().delete()

        bucket.delete()
        console.print(f"[green]Bucket '{name}' deleted successfully![/green]")

    except Exception as e:
        console.print(f"[red]Failed to delete bucket: {e}[/red]")
        raise typer.Exit(1)


@app.command("static-site")
def configure_static_site(
    name: str = typer.Argument(..., help="Bucket name"),
    index: str = typer.Option("index.html", "--index", "-i", help="Index document"),
    error: str = typer.Option("error.html", "--error", "-e", help="Error document"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Configure bucket for static website hosting."""
    client = boto3.client("s3", region_name=region)

    try:
        # Enable static website hosting
        client.put_bucket_website(
            Bucket=name,
            WebsiteConfiguration={
                "IndexDocument": {"Suffix": index},
                "ErrorDocument": {"Key": error}
            }
        )

        # Remove public access block
        client.delete_public_access_block(Bucket=name)

        # Set bucket policy for public read
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{name}/*"
                }
            ]
        }

        client.put_bucket_policy(
            Bucket=name,
            Policy=json.dumps(bucket_policy)
        )

        # Get website endpoint
        if region == "us-east-1":
            endpoint = f"http://{name}.s3-website-{region}.amazonaws.com"
        else:
            endpoint = f"http://{name}.s3-website.{region}.amazonaws.com"

        console.print(f"[green]Static website hosting enabled![/green]")
        console.print(f"Website URL: {endpoint}")

    except Exception as e:
        console.print(f"[red]Failed to configure static site: {e}[/red]")
        raise typer.Exit(1)


@app.command("upload")
def upload_files(
    name: str = typer.Argument(..., help="Bucket name"),
    source: str = typer.Option(..., "--source", "-s", help="Local path to upload"),
    prefix: str = typer.Option("", "--prefix", "-p", help="S3 key prefix"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Upload directory recursively"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Upload files to S3 bucket."""
    import os
    s3 = boto3.client("s3", region_name=region)

    try:
        if recursive and os.path.isdir(source):
            for root, dirs, files in os.walk(source):
                for file in files:
                    local_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_path, source)
                    s3_key = os.path.join(prefix, relative_path) if prefix else relative_path

                    # Determine content type
                    content_type = _get_content_type(file)

                    s3.upload_file(
                        local_path, name, s3_key,
                        ExtraArgs={"ContentType": content_type}
                    )
                    console.print(f"Uploaded: {s3_key}")

            console.print(f"[green]Upload complete![/green]")
        else:
            filename = os.path.basename(source)
            s3_key = os.path.join(prefix, filename) if prefix else filename
            content_type = _get_content_type(filename)

            s3.upload_file(
                source, name, s3_key,
                ExtraArgs={"ContentType": content_type}
            )
            console.print(f"[green]Uploaded: {s3_key}[/green]")

    except Exception as e:
        console.print(f"[red]Failed to upload: {e}[/red]")
        raise typer.Exit(1)


@app.command("sync")
def sync_files(
    name: str = typer.Argument(..., help="Bucket name"),
    source: str = typer.Option(..., "--source", "-s", help="Local directory to sync"),
    prefix: str = typer.Option("", "--prefix", "-p", help="S3 key prefix"),
    delete: bool = typer.Option(False, "--delete", help="Delete files in S3 not in source"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Sync local directory to S3 bucket."""
    import subprocess

    try:
        cmd = ["aws", "s3", "sync", source, f"s3://{name}/{prefix}"]
        if delete:
            cmd.append("--delete")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            console.print(f"[green]Sync complete![/green]")
            if result.stdout:
                console.print(result.stdout)
        else:
            console.print(f"[red]Sync failed: {result.stderr}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Failed to sync: {e}[/red]")
        raise typer.Exit(1)


def _get_content_type(filename: str) -> str:
    """Get content type based on file extension."""
    import mimetypes
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or "application/octet-stream"


@app.command("cors")
def configure_cors(
    name: str = typer.Argument(..., help="Bucket name"),
    origins: str = typer.Option("*", "--origins", help="Allowed origins (comma-separated)"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Configure CORS for S3 bucket."""
    client = boto3.client("s3", region_name=region)

    try:
        cors_config = {
            "CORSRules": [
                {
                    "AllowedHeaders": ["*"],
                    "AllowedMethods": ["GET", "HEAD"],
                    "AllowedOrigins": origins.split(","),
                    "ExposeHeaders": ["ETag"],
                    "MaxAgeSeconds": 3000
                }
            ]
        }

        client.put_bucket_cors(
            Bucket=name,
            CORSConfiguration=cors_config
        )
        console.print(f"[green]CORS configured for bucket '{name}'[/green]")

    except Exception as e:
        console.print(f"[red]Failed to configure CORS: {e}[/red]")
        raise typer.Exit(1)
