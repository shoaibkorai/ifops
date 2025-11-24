#!/bin/bash

# IFOps Installation Script
# This script sets up IFOps CLI tool

set -e

echo "================================"
echo "  IFOps Installation Script"
echo "================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo "❌ Python 3.9 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "  Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip -q
echo "✓ Pip upgraded"

# Install package
echo ""
echo "Installing IFOps..."
pip install -e . -q
echo "✓ IFOps installed"

# Create ~/.ifops directory and credentials file
echo ""
IFOPS_DIR="$HOME/.ifops"
CREDS_FILE="$IFOPS_DIR/credentials"

if [ ! -d "$IFOPS_DIR" ]; then
    mkdir -p "$IFOPS_DIR"
    echo "✓ Created config directory: $IFOPS_DIR"
else
    echo "✓ Config directory already exists: $IFOPS_DIR"
fi

if [ ! -f "$CREDS_FILE" ]; then
    touch "$CREDS_FILE"
    chmod 600 "$CREDS_FILE"
    echo "✓ Created credentials file: $CREDS_FILE"
else
    echo "✓ Credentials file already exists: $CREDS_FILE"
fi

# Verify installation
echo ""
echo "Verifying installation..."
if ifops version &> /dev/null; then
    echo "✓ IFOps installed successfully!"
else
    echo "❌ Installation verification failed"
    exit 1
fi

echo ""
echo "================================"
echo "  Installation Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo ""
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Setup your AWS credentials:"
echo "     ifops configure --setup"
echo ""
echo "  3. Verify your credentials:"
echo "     ifops --profile <profile-name> configure --verify"
echo ""
echo "  4. Run commands:"
echo "     ifops --profile <profile-name> s3 list"
echo "     ifops --profile <profile-name> ec2 list"
echo ""
echo "  Credentials are stored in: $CREDS_FILE"
echo ""
