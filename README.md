# IFOps - AWS Infrastructure Management CLI

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful command-line tool for managing AWS infrastructure including EC2, ECS, ECR, S3, App Runner, Amplify, SSL certificates, and CI/CD pipelines.

## Features

- **EC2 Management** - Create, modify, start, stop, and terminate EC2 instances
- **ECS Management** - Manage clusters, task definitions, and services
- **ECR Management** - Create repositories, manage images, Docker login
- **S3 Management** - Bucket operations, static website hosting, file sync
- **App Runner** - Deploy containerized applications
- **Amplify** - Deploy frontend applications
- **SSL Certificates** - Request, manage, and auto-renew ACM certificates
- **CI/CD Pipelines** - Build and deploy to ECR, ECS, S3, Amplify

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ifops.git
cd ifops

# Run the install script
./install.sh
```

The Script will:
- Check Python version (3.9+ required)
- Create a virtual environment
- Install all dependencies
- Create `~/.ifops/` directory for credentials
- Verify the installation

## Quick Start

### Configure AWS Credentials

**Option 1: Interactive Setup (Recommended)**

```bash
# Activate virtual environment
source venv/bin/activate

# Setup credentials interactively
ifops configure --setup

# This will prompt for:
# - AWS Access Key ID
# - AWS Secret Access Key
# - AWS Region
# - Profile Name (e.g., default, production)

# Verify credentials
ifops configure --verify --profile default
```

**Option 2: Use existing AWS credentials**

If you already have `~/.aws/credentials`, IFOps will use them automatically.

**Configuration Commands:**

```bash
# Show current configuration and all profiles
ifops configure

# Setup new credentials interactively
ifops configure --setup

# Verify credentials work with AWS
ifops configure --verify --profile my-profile

# Use a specific profile with any command
ifops ecr list --profile production
ifops ec2 list --profile staging --region eu-west-1
```

### Basic Usage

```bash
# Show help
ifops --help

# Show version
ifops version

# List EC2 instances
ifops ec2 list

# List S3 buckets
ifops s3 list

# Create ECR repository
ifops ecr create my-app --scan

# Deploy to App Runner
ifops apprunner create my-service --image 123456789.dkr.ecr.us-east-1.amazonaws.com/my-app:latest --role arn:aws:iam::123456789:role/AppRunnerRole
```

## Command Reference

### EC2 Commands

```bash
ifops ec2 create my-instance --ami ami-0123456789 --type t3.micro --key my-key
ifops ec2 list [--state running]
ifops ec2 start i-1234567890abcdef0
ifops ec2 stop i-1234567890abcdef0
ifops ec2 terminate i-1234567890abcdef0 --force
ifops ec2 modify i-1234567890abcdef0 --type t3.small
ifops ec2 status i-1234567890abcdef0
```

### ECS Commands

```bash
ifops ecs create-cluster my-cluster
ifops ecs list-clusters
ifops ecs register-task my-task --container app --image my-image:latest --execution-role arn:aws:iam::...
ifops ecs create-service my-cluster --name my-service --task-def my-task:1 --subnets subnet-xxx --sg sg-xxx
ifops ecs list-services my-cluster
ifops ecs update-service my-cluster --service my-service --force
ifops ecs run-task my-cluster --task-def my-task:1 --subnets subnet-xxx --sg sg-xxx
```

### ECR Commands

```bash
ifops ecr create my-repo [--scan] [--immutable]
ifops ecr list
ifops ecr delete my-repo [--force]
ifops ecr login
ifops ecr images my-repo
ifops ecr delete-image my-repo --tag v1.0.0
```

### S3 Commands

```bash
ifops s3 create my-bucket [--versioning] [--public]
ifops s3 list
ifops s3 delete my-bucket [--force]
ifops s3 static-site my-bucket --index index.html --error error.html
ifops s3 upload my-bucket --source ./dist --recursive
ifops s3 sync my-bucket --source ./dist [--delete]
ifops s3 cors my-bucket --origins "*"
```

### App Runner Commands

```bash
ifops apprunner create my-service --image ecr-image-uri --role role-arn
ifops apprunner list
ifops apprunner delete service-arn
ifops apprunner deploy service-arn
ifops apprunner status service-arn
```

### Amplify Commands

```bash
ifops amplify create my-app --repo https://github.com/user/repo --token github-token
ifops amplify list
ifops amplify delete app-id
ifops amplify deploy app-id [--branch main]
ifops amplify status app-id
ifops amplify domain app-id --domain example.com
```

### SSL Commands

```bash
ifops ssl request example.com [--alt-names www.example.com]
ifops ssl list
ifops ssl status certificate-arn
ifops ssl delete certificate-arn
ifops ssl renew certificate-arn
ifops ssl import --cert cert.pem --key key.pem
ifops ssl auto-renew
ifops ssl validate-dns certificate-arn --zone hosted-zone-id
```

### CI/CD Commands

```bash
# Build and push to ECR
ifops cicd ecr-push my-repo --tag v1.0.0 --dockerfile Dockerfile

# Deploy to various services
ifops cicd deploy-ecs my-cluster --service my-service --force
ifops cicd deploy-apprunner service-arn
ifops cicd deploy-amplify app-id --branch main
ifops cicd deploy-s3 my-bucket --source ./dist [--cf-dist distribution-id]

# CodePipeline management
ifops cicd create-pipeline my-pipeline --repo owner/repo --connection conn-arn --ecr my-repo --cluster my-cluster --service my-service --role role-arn --artifact-bucket bucket
ifops cicd list-pipelines
ifops cicd trigger my-pipeline
ifops cicd status my-pipeline
```

### Project Commands (Declarative Mode)

IFOps supports Terraform-like declarative infrastructure management. Define your infrastructure in `infra.yaml` and let IFOps manage the state.

```bash
# Create a new project (creates infra.yaml in current directory)
ifops project create my-app --region eu-west-3

# Show available resource types
ifops project resources

# List all projects
ifops project list

# Show project details
ifops project show my-app

# Plan changes (shows what will be created/destroyed)
ifops project plan my-app

# Apply changes
ifops project apply my-app [--auto-approve]

# Destroy all resources
ifops project destroy my-app [--auto-approve]

# Delete project (config and state)
ifops project delete my-app [--force]
```

**Example infra.yaml:**

```yaml
name: my-web-app
description: Production web application
region: eu-west-3

resources:
  - type: ecr
    name: my-app-repo
    scan_on_push: true

  - type: s3
    name: my-app-assets
    versioning: true
    static_site: true

  - type: ec2
    name: my-app-server
    ami: ami-00983e8a26e4c9bd9
    instance_type: t3.small
    key_name: my-key
```

See [docs/RESOURCES.md](docs/RESOURCES.md) for complete resource documentation.

## Project Structure

```
ifops/
├── ifops/                      # Main package
│   ├── __init__.py            # Package metadata
│   ├── main.py                # CLI entry point
│   ├── commands/              # Command modules
│   │   ├── apprunner.py
│   │   ├── amplify.py
│   │   ├── cicd.py
│   │   ├── ec2.py
│   │   ├── ecr.py
│   │   ├── ecs.py
│   │   ├── project.py         # Declarative infrastructure
│   │   ├── s3.py
│   │   └── ssl.py
│   ├── core/                  # Core functionality
│   │   ├── aws_client.py      # AWS client factory
│   │   ├── config.py          # Configuration management
│   │   └── exceptions.py      # Custom exceptions
│   └── utils/                 # Utilities
│       ├── helpers.py         # Helper functions
│       └── logger.py          # Logging setup
├── tests/                     # Test suite
│   ├── unit/
│   └── integration/
├── docs/                      # Documentation
├── pyproject.toml             # Project configuration
├── Makefile                   # Build automation
├── LICENSE
├── README.md
└── CONTRIBUTING.md
```

## Development

### Running Tests

```bash
make test
# or
pytest tests/ -v --cov=ifops
```

### Code Formatting

```bash
make format
# or
black ifops tests
isort ifops tests
```

### Linting

```bash
make lint
# or
flake8 ifops tests
mypy ifops
```

## Configuration

IFOps stores configuration in `~/.ifops/`:

```
~/.ifops/
├── config.yaml         # Global settings
├── credentials         # AWS credentials (like ~/.aws/credentials)
└── projects/           # Project state files
    └── my-app/
        └── state.json  # Resource state tracking
```

**config.yaml:**
```yaml
aws:
  region: us-east-1
  profile: default
logging:
  level: INFO
```

**credentials:**
```ini
[default]
aws_access_key_id = AKIAXXXXXXXXXX
aws_secret_access_key = xxxxxxxxxxxxxxxx
region = us-east-1

[production]
aws_access_key_id = AKIAYYYYYYYY
aws_secret_access_key = yyyyyyyyyyyy
region = eu-west-3
```

Use profiles with any command:
```bash
ifops ecr list --profile production
ifops project apply my-app --profile production
```

## Requirements

- Python 3.9+
- AWS credentials configured (via environment variables or `~/.aws/credentials`)
- Docker (for container build/push commands only)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) guide.

## Author

Your Name - your.email@example.com

## Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)
- AWS SDK for Python ([Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html))
