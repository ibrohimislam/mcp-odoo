# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands
- Install: `pip install -e .`
- Run Server: `python run_server.py` or `odoo-mcp`
- Docker: `docker build -t mcp/odoo:latest -f Dockerfile .`

## Code Style
- Python 3.10+
- Black formatting (88 char line length)
- isort for imports (black profile)
- Typed code (mypy: disallow_untyped_defs=true)
- Snake_case for variables/functions, PascalCase for classes
- Meaningful variable names and docstrings
- Detailed error handling with specific exception types

## Testing
- Add pytest tests for new functionality
- Run tests with `pytest`
- For single test: `pytest path/to/test.py::test_function_name -v`

## Before Committing
- Run linters: `black . && isort . && ruff check . && mypy .`
- Update CHANGELOG.md for significant changes