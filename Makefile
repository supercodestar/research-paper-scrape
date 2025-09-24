# Research Paper Scraper Makefile

.PHONY: help setup test lint run clean install-deps install-playwright

# Default target
help:
	@echo "Available targets:"
	@echo "  setup          - Install dependencies and setup environment"
	@echo "  test           - Run all tests"
	@echo "  lint           - Run linting checks"
	@echo "  run            - Run the scraper with trial config"
	@echo "  run-dry        - Run scraper in dry-run mode"
	@echo "  clean          - Clean generated files"
	@echo "  install-deps   - Install Python dependencies"
	@echo "  install-playwright - Install Playwright browsers"

# Setup environment
setup: install-deps install-playwright
	@echo "Environment setup complete!"

# Install Python dependencies
install-deps:
	pip install -e .

# Install Playwright browsers
install-playwright:
	python -m playwright install chromium

# Run tests
test:
	python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Run linting
lint:
	python -m flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503
	python -m mypy src/ --ignore-missing-imports

# Run scraper in trial mode
run:
	python -m scrape.cli trial --config configs/trial.yaml --limit 10

# Run scraper in dry-run mode
run-dry:
	python -m scrape.cli trial --config configs/trial.yaml --limit 10 --dry-run

# Run full scraper
run-full:
	python -m scrape.cli run --config configs/trial.yaml

# Clean generated files
clean:
	rm -rf data/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Development setup
dev-setup: setup
	@echo "Installing development dependencies..."
	pip install pytest pytest-cov flake8 mypy
	@echo "Development environment ready!"

# Check code quality
check: lint test
	@echo "Code quality checks passed!"

# Format code (if you add black)
format:
	@echo "Formatting code with black..."
	python -m black src/ tests/ --line-length=100

# Security check (if you add bandit)
security:
	@echo "Running security checks..."
	python -m bandit -r src/ -f json -o security-report.json || true
	@echo "Security check complete. See security-report.json for details."

# Build documentation (if you add sphinx)
docs:
	@echo "Building documentation..."
	@echo "Documentation build not implemented yet."

# Docker build (if you add Dockerfile)
docker-build:
	@echo "Building Docker image..."
	@echo "Docker build not implemented yet."

# Show help
.DEFAULT_GOAL := help
