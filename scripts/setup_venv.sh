#!/usr/bin/env bash
# Create .venv using 'uv' if available, otherwise use python -m venv
set -euo pipefail

VENV_DIR=".venv"

if command -v uv >/dev/null 2>&1; then
  echo "Creating virtualenv with uv..."
  # Try common uv subcommands; fall back to python venv if they don't work
  if uv venv .venv >/dev/null 2>&1; then
    :
  elif uv v .venv >/dev/null 2>&1; then
    :
  elif uv create .venv >/dev/null 2>&1; then
    :
  else
    echo "uv found but couldn't create venv with known subcommands; falling back to python -m venv"
    python -m venv "$VENV_DIR"
  fi
else
  echo "uv not found; falling back to python -m venv"
  python -m venv "$VENV_DIR"
fi

echo "Created $VENV_DIR"

# Print activation instruction for zsh
echo "To activate: source $VENV_DIR/bin/activate"

if [ -f requirements.txt ]; then
  echo "Installing requirements into virtualenv..."
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  pip install -r requirements.txt
  deactivate
  echo "Requirements installed. Activate with: source $VENV_DIR/bin/activate"
fi
