# IFOps Resource Reference

This document describes all available resource types for use in `infra.yaml` declarative configuration files.

## Quick Reference

| Type | Description | Required Properties |
|------|-------------|---------------------|
| `ecr` | ECR Repository | `name` |
| `s3` | S3 Bucket | `name` |
| `ec2` | EC2 Instance | `name`, `ami` |
| `ecs-cluster` | ECS Cluster | `name` |

---

## ECR Repository

Creates an Amazon Elastic Container Registry repository.

### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `name` | string | ✅ | - | Repository name |
| `scan_on_push` | boolean | ❌ | `true` | Enable image vulnerability scanning |
| `immutable` | boolean | ❌ | `false` | Enable tag immutability |
| `encryption` | string | ❌ | `AES256` | Encryption type (AES256, KMS) |

### Example

```yaml
resources:
  - type: ecr
    name: my-app-repo
    scan_on_push: true
    immutable: false
```

---

## S3 Bucket

Creates an Amazon S3 bucket for object storage.

### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `name` | string | ✅ | - | Bucket name (must be globally unique) |
| `versioning` | boolean | ❌ | `false` | Enable versioning |
| `static_site` | boolean | ❌ | `false` | Enable static website hosting |
| `public` | boolean | ❌ | `false` | Allow public access |
| `cors_origins` | list | ❌ | - | CORS allowed origins |

### Example

```yaml
resources:
  - type: s3
    name: my-app-assets-bucket
    versioning: true
    static_site: true
```

---

## EC2 Instance

Creates an Amazon EC2 virtual server instance.

### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `name` | string | ✅ | - | Instance name tag |
| `ami` | string | ✅ | - | AMI ID |
| `instance_type` | string | ❌ | `t3.micro` | Instance type |
| `key_name` | string | ❌ | - | SSH key pair name |
| `security_groups` | list | ❌ | - | Security group IDs |
| `subnet_id` | string | ❌ | - | Subnet ID |
| `volume_size` | integer | ❌ | `8` | Root volume size in GB |
| `user_data` | string | ❌ | - | Path to user data script |

### Example

```yaml
resources:
  - type: ec2
    name: my-web-server
    ami: ami-0123456789abcdef0
    instance_type: t3.small
    key_name: my-ssh-key
    security_groups:
      - sg-0123456789abcdef0
    subnet_id: subnet-0123456789abcdef0
    volume_size: 20
```

### Common AMI IDs

| Region | Amazon Linux 2023 | Ubuntu 22.04 |
|--------|-------------------|--------------|
| us-east-1 | ami-0c7217cdde317cfec | ami-0c7217cdde317cfec |
| eu-west-1 | ami-0694d931cee176e7d | ami-0694d931cee176e7d |
| eu-west-3 | ami-00983e8a26e4c9bd9 | ami-00983e8a26e4c9bd9 |

---

## ECS Cluster

Creates an Amazon ECS cluster for container orchestration.

### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `name` | string | ✅ | - | Cluster name |
| `capacity_providers` | list | ❌ | `[FARGATE, FARGATE_SPOT]` | Capacity providers |
| `container_insights` | boolean | ❌ | `true` | Enable Container Insights |

### Example

```yaml
resources:
  - type: ecs-cluster
    name: my-app-cluster
    capacity_providers:
      - FARGATE
      - FARGATE_SPOT
```

---

## Complete Example

Here's a complete `infra.yaml` for a typical web application:

```yaml
name: my-web-app
description: Production web application infrastructure
region: eu-west-3

resources:
  # Container registry for Docker images
  - type: ecr
    name: my-web-app-repo
    scan_on_push: true

  # Static assets bucket
  - type: s3
    name: my-web-app-assets
    versioning: true
    static_site: true

  # Application server
  - type: ec2
    name: my-web-app-server
    ami: ami-00983e8a26e4c9bd9
    instance_type: t3.medium
    key_name: production-key
    volume_size: 50

  # Container orchestration
  - type: ecs-cluster
    name: my-web-app-cluster
```

---

## Commands

```bash
# Create a new project
ifops project create my-project --region eu-west-3

# View available resources
ifops project resources

# Plan changes
ifops project plan my-project --profile my-profile

# Apply changes
ifops project apply my-project --profile my-profile

# Destroy all resources
ifops project destroy my-project --profile my-profile
```

---

## State Management

- **State file location**: `~/.ifops/projects/<project-name>/state.json`
- **Config file location**: `./infra.yaml` (in your project directory)

The state file tracks:
- Created resources and their IDs
- Creation timestamps
- Config file path

---

## Best Practices

1. **Use descriptive names**: Resource names should clearly indicate their purpose
2. **Enable versioning**: For S3 buckets storing important data
3. **Enable scanning**: For ECR repositories to detect vulnerabilities
4. **Use appropriate instance types**: Start small and scale up as needed
5. **Tag resources**: Use the `name` property consistently for easy identification
