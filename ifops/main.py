#!/usr/bin/env python3
"""
IFOps CLI - AWS Infrastructure Management Tool

Main entry point for the CLI application.
"""

import typer
from typing import Optional
from rich.console import Console

from ifops import __version__
from ifops.commands import apprunner, amplify, ecr, ec2, ecs, s3, cicd, ssl, project
from ifops.core.config import (
    load_config, save_config, get_config_dir,
    load_credentials, save_credentials, list_profiles, apply_profile,
    CREDENTIALS_FILE
)
from ifops.utils.logger import setup_logging

# Initialize console and app
console = Console()
app = typer.Typer(
    name="ifops",
    help="IFOps - AWS Infrastructure Management CLI",
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"allow_interspersed_args": True}
)

# Register command groups
app.add_typer(apprunner.app, name="apprunner", help="App Runner deployment management")
app.add_typer(amplify.app, name="amplify", help="Amplify deployment management")
app.add_typer(ecr.app, name="ecr", help="ECR repository management")
app.add_typer(ec2.app, name="ec2", help="EC2 instance management")
app.add_typer(ecs.app, name="ecs", help="ECS cluster/task/service management")
app.add_typer(s3.app, name="s3", help="S3 bucket management and static site hosting")
app.add_typer(cicd.app, name="cicd", help="CI/CD pipeline management")
app.add_typer(ssl.app, name="ssl", help="SSL certificate management")
app.add_typer(project.app, name="project", help="Declarative infrastructure projects (like Terraform)")


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold cyan]IFOps CLI[/bold cyan] v{__version__}")


@app.command()
def configure(
    profile: str = typer.Option(None, "--profile", "-p", help="AWS profile to use"),
    region: str = typer.Option(None, "--region", "-r", help="AWS region"),
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    verify: bool = typer.Option(False, "--verify", "-v", help="Verify AWS credentials"),
    setup: bool = typer.Option(False, "--setup", help="Setup new AWS credentials interactively")
):
    """Configure AWS credentials and default settings."""
    import os
    config = load_config()

    if setup:
        # Interactive credential setup
        console.print("[bold]AWS Credentials Setup[/bold]\n")

        access_key = typer.prompt("AWS Access Key ID")
        secret_key = typer.prompt("AWS Secret Access Key", hide_input=True)
        region_input = typer.prompt("AWS Region", default="us-east-1")
        profile_input = typer.prompt("AWS Profile Name", default="default")

        # Save to ~/.ifops/credentials
        save_credentials(profile_input, access_key, secret_key, region_input)

        console.print(f"\n[green]✓ Credentials saved to {CREDENTIALS_FILE}[/green]")
        console.print(f"  Profile: {profile_input}")
        console.print("\nTo use them, run:")
        console.print(f"  [cyan]ifops --profile {profile_input} <command>[/cyan]")
        console.print(f"  [cyan]ifops configure --verify --profile {profile_input}[/cyan]")
        return

    if show or (not profile and not region and not verify):
        console.print("[bold]Current Configuration:[/bold]")
        console.print(f"  Config directory: {get_config_dir()}")
        console.print(f"  Credentials file: {CREDENTIALS_FILE}")

        # Show configured profiles
        profiles = list_profiles()
        if profiles:
            console.print(f"\n[bold]Configured Profiles:[/bold]")
            for p in profiles:
                creds = load_credentials(p)
                masked_key = creds['aws_access_key_id'][:4] + '*' * 12 + creds['aws_access_key_id'][-4:] if creds.get('aws_access_key_id') else 'N/A'
                console.print(f"  [{p}]")
                console.print(f"    Access Key: {masked_key}")
                console.print(f"    Region: {creds.get('region', 'us-east-1')}")
        else:
            console.print(f"\n[yellow]No profiles configured. Run: ifops configure --setup[/yellow]")

        # Show current environment
        console.print("\n[bold]Current Environment:[/bold]")
        access_key = os.environ.get('AWS_ACCESS_KEY_ID', '')
        if access_key:
            masked_key = access_key[:4] + '*' * (len(access_key) - 8) + access_key[-4:]
            console.print(f"  AWS_ACCESS_KEY_ID: {masked_key}")
        else:
            console.print("  AWS_ACCESS_KEY_ID: [dim]not set[/dim]")

        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
        if secret_key:
            console.print(f"  AWS_SECRET_ACCESS_KEY: {'*' * 20}")
        else:
            console.print("  AWS_SECRET_ACCESS_KEY: [dim]not set[/dim]")

        env_region = os.environ.get('AWS_DEFAULT_REGION', '')
        console.print(f"  AWS_DEFAULT_REGION: {env_region or '[dim]not set[/dim]'}")
        return

    if verify:
        # Verify AWS credentials
        import boto3
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            console.print("[green]✓ AWS credentials are valid![/green]")
            console.print(f"  Account: {identity['Account']}")
            console.print(f"  User ARN: {identity['Arn']}")
            console.print(f"  User ID: {identity['UserId']}")
        except Exception as e:
            console.print(f"[red]✗ AWS credentials verification failed: {e}[/red]")
        return

    if profile:
        config["aws"]["profile"] = profile
        console.print(f"[green]Set AWS profile: {profile}[/green]")

    if region:
        config["aws"]["region"] = region
        console.print(f"[green]Set AWS region: {region}[/green]")

    save_config(config)
    console.print("[green]Configuration saved![/green]")


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
    profile: str = typer.Option(None, "--profile", "-p", help="AWS profile to use from ~/.ifops/credentials")
):
    """
    IFOps - AWS Infrastructure Management CLI

    Manage AWS resources including EC2, ECS, ECR, S3, App Runner,
    Amplify, SSL certificates, and CI/CD pipelines.
    """
    if debug:
        setup_logging("DEBUG")
    elif verbose:
        setup_logging("INFO")
    else:
        setup_logging("WARNING")

    # Apply profile credentials if specified
    if profile:
        creds = load_credentials(profile)
        if creds:
            apply_profile(profile)
        else:
            console.print(f"[red]Profile '{profile}' not found in {CREDENTIALS_FILE}[/red]")
            console.print(f"Available profiles: {', '.join(list_profiles()) or 'none'}")
            raise typer.Exit(1)


def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
