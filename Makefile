# VoiceClone Pro - Makefile
.PHONY: help install dev test build docker clean deploy

# Variables
PYTHON = python3
PIP = pip3
FLASK_APP = app.py
DOCKER_COMPOSE = docker-compose
PROJECT_NAME = voiceclone-pro

# Default target
help:
	@echo "VoiceClone Pro - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install     Install dependencies"
	@echo "  dev         Run development server"
	@echo "  test        Run tests"
	@echo "  lint        Run code linting"
	@echo "  format      Format code"
	@echo ""
	@echo "Production:"
	@echo "  build       Build for production"
	@echo "  docker      Build and run Docker containers"
	@echo "  deploy      Deploy to production"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean       Clean temporary files"
	@echo "  backup      Backup database and models"
	@echo "  logs        View application logs"

# Development commands
install:
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Creating necessary directories..."
	mkdir -p uploads outputs models logs temp
	@echo "Installation complete!"

dev:
	@echo "Starting development server..."
	export FLASK_ENV=development && $(PYTHON) $(FLASK_APP)

dev-frontend:
	@echo "Starting frontend development server..."
	npm install
	npm run dev

test:
	@echo "Running tests..."
	$(PYTHON) -m pytest tests/ -v --cov=. --cov-report=html

test-watch:
	@echo "Running tests in watch mode..."
	$(PYTHON) -m pytest-watch tests/

lint:
	@echo "Running linting..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format:
	@echo "Formatting code..."
	black .
	isort .

type-check:
	@echo "Running type checking..."
	mypy . --ignore-missing-imports

# Production commands
build:
	@echo "Building for production..."
	mkdir -p dist
	$(PIP) install --upgrade build
	$(PYTHON) -m build
	@echo "Build complete!"

docker:
	@echo "Building and starting Docker containers..."
	$(DOCKER_COMPOSE) up --build -d
	@echo "Docker containers started!"

docker-logs:
	@echo "Viewing Docker logs..."
	$(DOCKER_COMPOSE) logs -f

docker-stop:
	@echo "Stopping Docker containers..."
	$(DOCKER_COMPOSE) down

docker-clean:
	@echo "Cleaning Docker containers and images..."
	$(DOCKER_COMPOSE) down -v --rmi all

# Database commands
db-init:
	@echo "Initializing database..."
	$(PYTHON) -c "from app import db; db.create_all()"

db-migrate:
	@echo "Running database migrations..."
	flask db migrate -m "Auto migration"
	flask db upgrade

db-reset:
	@echo "Resetting database..."
	$(PYTHON) -c "from app import db; db.drop_all(); db.create_all()"

# Backup and restore
backup:
	@echo "Creating backup..."
	mkdir -p backups
	tar -czf backups/backup-$(shell date +%Y%m%d-%H%M%S).tar.gz uploads/ outputs/ models/ voiceclone.db
	@echo "Backup created in backups/ directory"

restore:
	@echo "To restore from backup, run:"
	@echo "tar -xzf backups/backup-YYYYMMDD-HHMMSS.tar.gz"

# Monitoring and logs
logs:
	@echo "Viewing application logs..."
	tail -f logs/voiceclone.log

logs-error:
	@echo "Viewing error logs..."
	tail -f logs/error.log

monitor:
	@echo "Starting monitoring dashboard..."
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000 (admin/admin)"

# Maintenance
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf temp/*
	@echo "Cleanup complete!"

clean-uploads:
	@echo "Cleaning old upload files..."
	find uploads/ -type f -mtime +7 -delete
	@echo "Old uploads cleaned!"

clean-outputs:
	@echo "Cleaning old output files..."
	find outputs/ -type f -mtime +1 -delete
	@echo "Old outputs cleaned!"

# Security
security-check:
	@echo "Running security checks..."
	$(PIP) install safety bandit
	safety check
	bandit -r . -f json -o security-report.json

# Performance
profile:
	@echo "Running performance profiling..."
	$(PYTHON) -m cProfile -o profile.stats app.py

benchmark:
	@echo "Running benchmarks..."
	$(PYTHON) tests/benchmark.py

# Deployment
deploy-staging:
	@echo "Deploying to staging..."
	git push staging main
	@echo "Deployed to staging!"

deploy-production:
	@echo "Deploying to production..."
	@echo "WARNING: This will deploy to production. Continue? [y/N]"
	@read confirm && [ "$confirm" = "y" ] || exit 1
	git push production main
	@echo "Deployed to production!"

# GitHub Actions
github-setup:
	@echo "Setting up GitHub Actions..."
	mkdir -p .github/workflows
	@echo "GitHub Actions setup complete!"

# Documentation
docs:
	@echo "Generating documentation..."
	$(PIP) install sphinx sphinx-rtd-theme
	sphinx-build -b html docs/ docs/_build/
	@echo "Documentation generated in docs/_build/"

docs-serve:
	@echo "Serving documentation..."
	$(PYTHON) -m http.server 8080 -d docs/_build/

# API Documentation
api-docs:
	@echo "Generating API documentation..."
	$(PYTHON) -c "from app import app; from flask import url_for; print('API docs available at /apidocs')"

# Environment setup
env-setup:
	@echo "Setting up environment..."
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

env-check:
	@echo "Checking environment variables..."
	$(PYTHON) -c "import os; print('SECRET_KEY:', 'SET' if os.getenv('SECRET_KEY') else 'NOT SET')"

# Version management
version:
	@echo "Current version:"
	@$(PYTHON) -c "print(open('VERSION').read().strip())" 2>/dev/null || echo "No version file found"

bump-version:
	@echo "Bumping version..."
	@read -p "Enter new version: " version && echo $version > VERSION
	@echo "Version updated to $(cat VERSION)"

# Quick start
quickstart: install env-setup db-init
	@echo ""
	@echo "🎉 VoiceClone Pro setup complete!"
	@echo ""
	@echo "Quick start commands:"
	@echo "  make dev          - Start development server"
	@echo "  make docker       - Start with Docker"
	@echo "  make test         - Run tests"
	@echo ""
	@echo "Visit http://localhost:5000 to get started!"

# Development workflow
dev-setup: install env-setup db-init
	@echo "Development environment ready!"

dev-reset: clean db-reset
	@echo "Development environment reset!"

# Production workflow
prod-setup: build docker
	@echo "Production environment ready!"

# All-in-one commands
all: clean install test lint build
	@echo "All tasks completed successfully!"

check: lint test security-check
	@echo "All checks passed!"
	@echo "
