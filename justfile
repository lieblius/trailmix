# This menu
help:
    @just --list

# Run all checks
check: lint types test

# Run linter
lint:
    uv run ruff check src/

# Fix lint issues and format
fix:
    uv run ruff check --fix src/
    uv run ruff format src/

# Format code
format:
    uv run ruff format src/

# Run typechecker
types:
    uv run ty check src/

# Run tests
test:
    uv run pytest tests/ -v

# Run integration test (init + sync dry-run against live API)
integration:
    #!/usr/bin/env bash
    set -e
    rm -rf /tmp/trailmix-test
    rm -rf ~/.config/trailmix
    mkdir /tmp/trailmix-test
    echo "y" | uv run trailmix init /tmp/trailmix-test
    uv run trailmix config
    uv run trailmix sync --dry-run

# Install dev dependencies
install:
    uv sync --group dev
