#!/bin/bash

set -e

# Script directory (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Find a python executable
if command -v python3 &> /dev/null; then
    PY_CMD="python3"
elif command -v python &> /dev/null; then
    PY_CMD="python"
else
    echo "Python 3 was not found in PATH. Please install Python 3 and try again."
    exit 1
fi

echo "Using Python: $PY_CMD"

# Prefer .venv, fall back to venv
if [ -d ".venv/bin/activate" ]; then
    VENV_DIR=".venv"
elif [ -d "venv/bin/activate" ]; then
    VENV_DIR="venv"
else
    VENV_DIR=".venv"
fi

# Create venv if it doesn't exist
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Creating virtual environment in '$VENV_DIR'..."
    $PY_CMD -m venv "$VENV_DIR" || {
        echo "Failed to create virtual environment using $PY_CMD."
        exit 1
    }
fi

# Activate the venv
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# If requirements.txt exists, install or upgrade packages as needed
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    python -m pip install --upgrade pip
    python -m pip install -r "$SCRIPT_DIR/requirements.txt"
else
    echo "No requirements.txt found in '$SCRIPT_DIR'. Skipping pip install."
fi

echo "Virtual environment is ready. Launching bash with venv activated..."
# Keep the shell open with the venv activated
exec bash --rcfile <(echo 'source '"$VENV_DIR/bin/activate"'
if [ -f ".bashrc" ]; then 
    source .bashrc
fi
echo "Virtual environment activated. You can now run Python commands. Type '\''exit'\'' to close this shell."')