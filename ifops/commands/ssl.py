"""SSL certificate management commands."""

import typer
import boto3
from typing import Optional
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("request")
def request_certificate(
    domain: str = typer.Argument(..., help="Primary domain name"),
    alt_names: str = typer.Option(None, "--alt-names", "-a", help="Alternative names (comma-separated)"),
    validation: str = typer.Option("DNS", "--validation", "-v", help="Validation method (DNS or EMAIL)"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Request a new ACM certificate."""
    client = boto3.client("acm", region_name=region)

    try:
        params = {
            "DomainName": domain,
            "ValidationMethod": validation
        }

        if alt_names:
            params["SubjectAlternativeNames"] = [domain] + alt_names.split(",")

        response = client.request_certificate(**params)

        console.print(f"[green]Certificate requested successfully![/green]")
        console.print(f"Certificate ARN: {response['CertificateArn']}")

        if validation == "DNS":
            # Get DNS validation records
            waiter = client.get_waiter("certificate_validated")
            console.print("\n[yellow]Waiting for certificate details...[/yellow]")

            import time
            time.sleep(5)  # Wait for certificate to be created

            cert_details = client.describe_certificate(CertificateArn=response["CertificateArn"])

            console.print("\n[bold]DNS Validation Records:[/bold]")
            for option in cert_details["Certificate"].get("DomainValidationOptions", []):
                if "ResourceRecord" in option:
                    record = option["ResourceRecord"]
                    console.print(f"\nDomain: {option['DomainName']}")
                    console.print(f"  Type: {record['Type']}")
                    console.print(f"  Name: {record['Name']}")
                    console.print(f"  Value: {record['Value']}")

    except Exception as e:
        console.print(f"[red]Failed to request certificate: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_certificates(
    status: str = typer.Option(None, "--status", "-s", help="Filter by status (PENDING_VALIDATION, ISSUED, etc)"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """List ACM certificates."""
    client = boto3.client("acm", region_name=region)

    try:
        params = {}
        if status:
            params["CertificateStatuses"] = [status]

        response = client.list_certificates(**params)

        table = Table(title="ACM Certificates")
        table.add_column("Domain", style="cyan")
        table.add_column("ARN", style="dim")
        table.add_column("Status", style="green")
        table.add_column("In Use", style="yellow")

        for cert in response.get("CertificateSummaryList", []):
            # Get full details for each certificate
            details = client.describe_certificate(CertificateArn=cert["CertificateArn"])
            cert_info = details["Certificate"]

            in_use = "Yes" if cert_info.get("InUseBy") else "No"

            table.add_row(
                cert["DomainName"],
                cert["CertificateArn"][-40:] + "...",
                cert_info["Status"],
                in_use
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to list certificates: {e}[/red]")
        raise typer.Exit(1)


@app.command("status")
def certificate_status(
    cert_arn: str = typer.Argument(..., help="Certificate ARN"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Get certificate status and details."""
    client = boto3.client("acm", region_name=region)

    try:
        response = client.describe_certificate(CertificateArn=cert_arn)
        cert = response["Certificate"]

        console.print(f"[bold]Certificate: {cert['DomainName']}[/bold]")
        console.print(f"Status: {cert['Status']}")
        console.print(f"Type: {cert['Type']}")

        if cert.get("NotBefore"):
            console.print(f"Valid From: {cert['NotBefore']}")
        if cert.get("NotAfter"):
            console.print(f"Valid Until: {cert['NotAfter']}")

        if cert.get("RenewalEligibility"):
            console.print(f"Renewal Eligibility: {cert['RenewalEligibility']}")

        if cert.get("SubjectAlternativeNames"):
            console.print(f"Alternative Names: {', '.join(cert['SubjectAlternativeNames'])}")

        if cert.get("InUseBy"):
            console.print(f"\nIn Use By:")
            for resource in cert["InUseBy"]:
                console.print(f"  - {resource}")

        # Show validation status
        if cert.get("DomainValidationOptions"):
            console.print("\n[bold]Validation Status:[/bold]")
            for option in cert["DomainValidationOptions"]:
                status = option.get("ValidationStatus", "N/A")
                color = "green" if status == "SUCCESS" else "yellow" if status == "PENDING_VALIDATION" else "red"
                console.print(f"  {option['DomainName']}: [{color}]{status}[/{color}]")

    except Exception as e:
        console.print(f"[red]Failed to get certificate status: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_certificate(
    cert_arn: str = typer.Argument(..., help="Certificate ARN to delete"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Delete an ACM certificate."""
    client = boto3.client("acm", region_name=region)

    try:
        client.delete_certificate(CertificateArn=cert_arn)
        console.print(f"[green]Certificate deleted successfully![/green]")

    except client.exceptions.ResourceInUseException:
        console.print(f"[red]Certificate is in use and cannot be deleted[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Failed to delete certificate: {e}[/red]")
        raise typer.Exit(1)


@app.command("renew")
def renew_certificate(
    cert_arn: str = typer.Argument(..., help="Certificate ARN to renew"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Manually trigger certificate renewal."""
    client = boto3.client("acm", region_name=region)

    try:
        client.renew_certificate(CertificateArn=cert_arn)
        console.print(f"[green]Certificate renewal initiated![/green]")

    except Exception as e:
        console.print(f"[red]Failed to renew certificate: {e}[/red]")
        raise typer.Exit(1)


@app.command("import")
def import_certificate(
    cert_file: str = typer.Option(..., "--cert", "-c", help="Path to certificate file (PEM)"),
    key_file: str = typer.Option(..., "--key", "-k", help="Path to private key file (PEM)"),
    chain_file: str = typer.Option(None, "--chain", help="Path to certificate chain file (PEM)"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Import a custom SSL certificate."""
    client = boto3.client("acm", region_name=region)

    try:
        with open(cert_file, "rb") as f:
            certificate = f.read()

        with open(key_file, "rb") as f:
            private_key = f.read()

        params = {
            "Certificate": certificate,
            "PrivateKey": private_key
        }

        if chain_file:
            with open(chain_file, "rb") as f:
                params["CertificateChain"] = f.read()

        response = client.import_certificate(**params)

        console.print(f"[green]Certificate imported successfully![/green]")
        console.print(f"Certificate ARN: {response['CertificateArn']}")

    except Exception as e:
        console.print(f"[red]Failed to import certificate: {e}[/red]")
        raise typer.Exit(1)


@app.command("auto-renew")
def check_auto_renewal(
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Check auto-renewal status for all certificates."""
    client = boto3.client("acm", region_name=region)

    try:
        response = client.list_certificates(CertificateStatuses=["ISSUED"])

        table = Table(title="Certificate Auto-Renewal Status")
        table.add_column("Domain", style="cyan")
        table.add_column("Expires", style="yellow")
        table.add_column("Renewal Status", style="green")
        table.add_column("Type", style="dim")

        for cert in response.get("CertificateSummaryList", []):
            details = client.describe_certificate(CertificateArn=cert["CertificateArn"])
            cert_info = details["Certificate"]

            renewal_status = cert_info.get("RenewalEligibility", "N/A")
            cert_type = cert_info.get("Type", "N/A")

            # Check renewal summary if available
            if cert_info.get("RenewalSummary"):
                renewal_status = cert_info["RenewalSummary"]["RenewalStatus"]

            expires = str(cert_info.get("NotAfter", "N/A"))

            table.add_row(
                cert["DomainName"],
                expires[:10] if expires != "N/A" else "N/A",
                renewal_status,
                cert_type
            )

        console.print(table)
        console.print("\n[dim]Note: AWS-issued certificates auto-renew automatically.[/dim]")
        console.print("[dim]Imported certificates must be renewed manually.[/dim]")

    except Exception as e:
        console.print(f"[red]Failed to check auto-renewal status: {e}[/red]")
        raise typer.Exit(1)


@app.command("validate-dns")
def create_dns_validation(
    cert_arn: str = typer.Argument(..., help="Certificate ARN"),
    hosted_zone_id: str = typer.Option(..., "--zone", "-z", help="Route53 hosted zone ID"),
    region: str = typer.Option(None, "--region", help="AWS region")
):
    """Create Route53 DNS records for certificate validation."""
    acm = boto3.client("acm", region_name=region)
    route53 = boto3.client("route53")

    try:
        cert_details = acm.describe_certificate(CertificateArn=cert_arn)

        changes = []
        for option in cert_details["Certificate"].get("DomainValidationOptions", []):
            if "ResourceRecord" in option:
                record = option["ResourceRecord"]
                changes.append({
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": record["Name"],
                        "Type": record["Type"],
                        "TTL": 300,
                        "ResourceRecords": [{"Value": record["Value"]}]
                    }
                })

        if changes:
            route53.change_resource_record_sets(
                HostedZoneId=hosted_zone_id,
                ChangeBatch={"Changes": changes}
            )
            console.print(f"[green]DNS validation records created in Route53![/green]")
            console.print(f"Created {len(changes)} record(s)")
        else:
            console.print("[yellow]No DNS validation records found[/yellow]")

    except Exception as e:
        console.print(f"[red]Failed to create DNS validation records: {e}[/red]")
        raise typer.Exit(1)
