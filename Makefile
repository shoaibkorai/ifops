.PHONY: install dev-install test lint format clean build publish help

# Default target
help:
	@echo "IFOps - AWS Infrastructure Management CLI"
	@echo ""
	@echo "Available commands:"
	@echo "  make install      Install the package"
	@echo "  make dev-install  Install with development dependencies"
	@echo "  make test         Run tests"
	@echo "  make lint         Run linters"
	@echo "  make format       Format code"
	@echo "  make clean        Clean build artifacts"
	@echo "  make build        Build distribution packages"
	@echo "  make publish      Publish to PyPI"

install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=ifops --cov-report=term-missing

lint:
	flake8 ifops tests
	mypy ifops
	black --check ifops tests
	isort --check-only ifops tests

format:
	black ifops tests
	isort ifops tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

publish: build
	twine upload dist/*
