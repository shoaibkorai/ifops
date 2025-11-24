# Contributing to IFOps

Thank you for your interest in contributing to IFOps!

## Getting Started (For New Team Members)

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/ifops.git
cd ifops

# Run the automated installer
./install.sh
```

The installer will:
- Check Python version (3.9+ required)
- Create virtual environment
- Install all dependencies
- Create `~/.ifops/` directory structure

### 2. Activate Environment

```bash
source venv/bin/activate
```

### 3. Configure AWS Credentials

```bash
# Interactive setup (stores in ~/.ifops/credentials)
ifops configure --setup

# Verify your credentials work
ifops configure --verify --profile default
```

### 4. Test Installation

```bash
# List ECR repositories
ifops ecr list --profile your-profile

# Show help
ifops --help
```

## Development Setup

For development work, install additional dependencies:

```bash
source venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Code Style

- We use **Black** for code formatting
- We use **isort** for import sorting
- We use **flake8** for linting
- Maximum line length is 100 characters

Run formatters:
```bash
make format
```

Run linters:
```bash
make lint
```

## Testing

Run tests with coverage:
```bash
make test
```

## Project Structure

```
ifops/
├── ifops/
│   ├── main.py           # CLI entry point
│   ├── commands/         # All CLI commands
│   │   ├── ec2.py
│   │   ├── ecr.py
│   │   ├── s3.py
│   │   ├── project.py    # Declarative mode
│   │   └── ...
│   ├── core/             # Core utilities
│   │   └── config.py     # Credential management
│   └── utils/
├── docs/
│   └── RESOURCES.md      # YAML resource reference
└── tests/
```

## Adding New Commands

1. Create a new command file in `ifops/commands/`
2. Register the command group in `ifops/main.py`:
   ```python
   from ifops.commands import your_command
   app.add_typer(your_command.app, name="your-cmd", help="Description")
   ```
3. Add tests in `tests/unit/`
4. Update documentation

## Adding New Resource Types (Declarative Mode)

To add a new resource type for `ifops project`:

1. Update `ifops/commands/project.py`:
   - Add to `_create_resource()` function
   - Add to `_destroy_resource()` function
   - Update `show_resources()` command

2. Update `docs/RESOURCES.md` with the new resource documentation

## Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature
   ```
2. Make your changes
3. Write/update tests
4. Run formatters and linters:
   ```bash
   make format && make lint
   ```
5. Ensure all tests pass:
   ```bash
   make test
   ```
6. Commit with clear message
7. Push and create PR

## Commit Messages

Use conventional commits:
- `feat: add new S3 lifecycle management command`
- `fix: handle empty response in EC2 list`
- `docs: update installation instructions`
- `test: add unit tests for SSL commands`
- `refactor: simplify credential loading`

## Common Tasks

### Working with Declarative Projects

```bash
# Create project in your app directory
cd /path/to/your-app
ifops project create my-app --region eu-west-3

# Edit infra.yaml
nano infra.yaml

# Plan and apply
ifops project plan my-app --profile your-profile
ifops project apply my-app --profile your-profile
```

### Running Commands with Different Profiles

```bash
# Use --profile anywhere in the command
ifops ec2 list --profile production
ifops --profile staging s3 list
```

## Troubleshooting

### "ifops: command not found"
```bash
source venv/bin/activate
```

### "Profile not found"
```bash
# Check available profiles
ifops configure

# Setup new profile
ifops configure --setup
```

### AWS Credentials Issues
```bash
# Verify credentials
ifops configure --verify --profile your-profile

# Check what's configured
ifops configure
```

## Questions?

Feel free to open an issue for any questions or concerns.
