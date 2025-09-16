# Colombian Intelligence & Language Learning Platform - Makefile
# Common development commands for the platform

.PHONY: help install test lint format clean dev prod docker

# Default target
help:
	@echo "Colombian Platform Development Commands"
	@echo "====================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install     Install all dependencies"
	@echo "  install-dev Install development dependencies"
	@echo "  setup-db    Setup database and run migrations"
	@echo ""
	@echo "Development Commands:"
	@echo "  dev         Start development environment"
	@echo "  dev-api     Start backend API only"
	@echo "  dev-web     Start frontend only"
	@echo "  dev-worker  Start background worker"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test        Run all tests"
	@echo "  test-api    Run backend tests only"
	@echo "  test-web    Run frontend tests only"
	@echo "  test-integration Run integration tests"
	@echo "  test-coverage Run tests with coverage report"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  lint        Run linting on all code"
	@echo "  format      Format all code"
	@echo "  type-check  Run type checking"
	@echo ""
	@echo "Data Commands:"
	@echo "  collect     Run data collection manually"
	@echo "  migrate     Run database migrations"
	@echo "  seed        Load seed data"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build Build Docker images"
	@echo "  docker-up   Start with Docker Compose"
	@echo "  docker-down Stop Docker services"
	@echo ""
	@echo "Production Commands:"
	@echo "  build       Build for production"
	@echo "  deploy      Deploy to production"
	@echo "  backup      Create database backup"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  clean       Clean temporary files"
	@echo "  logs        View application logs"
	@echo "  status      Check system status"

# Variables
PYTHON := python
PIP := pip
NPM := npm
PYTEST := pytest
DOCKER := docker
DOCKER_COMPOSE := docker-compose

# Colors for output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RESET := \033[0m

# Installation Commands
install: install-backend install-frontend
	@echo "$(GREEN)✓ All dependencies installed$(RESET)"

install-backend:
	@echo "$(BLUE)Installing backend dependencies...$(RESET)"
	cd backend && $(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Backend dependencies installed$(RESET)"

install-dev: install-backend-dev install-frontend-dev
	@echo "$(GREEN)✓ All development dependencies installed$(RESET)"

install-backend-dev:
	@echo "$(BLUE)Installing backend development dependencies...$(RESET)"
	cd backend && $(PIP) install -r requirements.txt -r requirements-dev.txt
	@echo "$(GREEN)✓ Backend dev dependencies installed$(RESET)"

install-frontend:
	@echo "$(BLUE)Installing frontend dependencies...$(RESET)"
	cd frontend && $(NPM) install
	@echo "$(GREEN)✓ Frontend dependencies installed$(RESET)"

install-frontend-dev:
	@echo "$(BLUE)Installing frontend development dependencies...$(RESET)"
	cd frontend && $(NPM) install
	@echo "$(GREEN)✓ Frontend dev dependencies installed$(RESET)"

# Database Setup
setup-db:
	@echo "$(BLUE)Setting up database...$(RESET)"
	createdb colombian_platform || echo "Database already exists"
	cd backend && $(PYTHON) manage.py migrate
	@echo "$(GREEN)✓ Database setup complete$(RESET)"

migrate:
	@echo "$(BLUE)Running database migrations...$(RESET)"
	cd backend && $(PYTHON) manage.py migrate
	@echo "$(GREEN)✓ Migrations complete$(RESET)"

seed:
	@echo "$(BLUE)Loading seed data...$(RESET)"
	cd backend && $(PYTHON) manage.py loaddata fixtures/initial_sources.json
	cd backend && $(PYTHON) manage.py loaddata fixtures/sample_data.json
	@echo "$(GREEN)✓ Seed data loaded$(RESET)"

# Development Commands
dev: dev-services dev-api dev-web
	@echo "$(GREEN)✓ Development environment started$(RESET)"

dev-services:
	@echo "$(BLUE)Starting supporting services...$(RESET)"
	$(DOCKER_COMPOSE) up -d postgres redis
	@echo "$(GREEN)✓ Services started$(RESET)"

dev-api:
	@echo "$(BLUE)Starting backend API...$(RESET)"
	cd backend && $(PYTHON) manage.py runserver &
	@echo "$(GREEN)✓ Backend API started on http://localhost:8000$(RESET)"

dev-web:
	@echo "$(BLUE)Starting frontend...$(RESET)"
	cd frontend && $(NPM) start &
	@echo "$(GREEN)✓ Frontend started on http://localhost:3000$(RESET)"

dev-worker:
	@echo "$(BLUE)Starting background worker...$(RESET)"
	cd backend && celery -A config worker -l info &
	@echo "$(GREEN)✓ Background worker started$(RESET)"

dev-scheduler:
	@echo "$(BLUE)Starting task scheduler...$(RESET)"
	cd backend && celery -A config beat -l info &
	@echo "$(GREEN)✓ Task scheduler started$(RESET)"

# Testing Commands
test: test-api test-web
	@echo "$(GREEN)✓ All tests completed$(RESET)"

test-api:
	@echo "$(BLUE)Running backend tests...$(RESET)"
	cd backend && $(PYTEST) tests/ -v
	@echo "$(GREEN)✓ Backend tests completed$(RESET)"

test-web:
	@echo "$(BLUE)Running frontend tests...$(RESET)"
	cd frontend && $(NPM) test -- --watchAll=false
	@echo "$(GREEN)✓ Frontend tests completed$(RESET)"

test-integration:
	@echo "$(BLUE)Running integration tests...$(RESET)"
	cd backend && $(PYTEST) tests/test_integration.py -v
	@echo "$(GREEN)✓ Integration tests completed$(RESET)"

test-coverage:
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	cd backend && $(PYTEST) tests/ --cov=. --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report generated$(RESET)"

test-scrapers:
	@echo "$(BLUE)Running scraper tests...$(RESET)"
	cd backend && $(PYTEST) tests/test_scrapers.py -v
	@echo "$(GREEN)✓ Scraper tests completed$(RESET)"

test-api-clients:
	@echo "$(BLUE)Running API client tests...$(RESET)"
	cd backend && $(PYTEST) tests/test_api_clients.py -v
	@echo "$(GREEN)✓ API client tests completed$(RESET)"

# Code Quality Commands
lint: lint-backend lint-frontend
	@echo "$(GREEN)✓ Linting completed$(RESET)"

lint-backend:
	@echo "$(BLUE)Linting backend code...$(RESET)"
	cd backend && flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	cd backend && flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "$(GREEN)✓ Backend linting completed$(RESET)"

lint-frontend:
	@echo "$(BLUE)Linting frontend code...$(RESET)"
	cd frontend && $(NPM) run lint
	@echo "$(GREEN)✓ Frontend linting completed$(RESET)"

format: format-backend format-frontend
	@echo "$(GREEN)✓ Code formatting completed$(RESET)"

format-backend:
	@echo "$(BLUE)Formatting backend code...$(RESET)"
	cd backend && black .
	cd backend && isort .
	@echo "$(GREEN)✓ Backend formatting completed$(RESET)"

format-frontend:
	@echo "$(BLUE)Formatting frontend code...$(RESET)"
	cd frontend && $(NPM) run format
	@echo "$(GREEN)✓ Frontend formatting completed$(RESET)"

type-check:
	@echo "$(BLUE)Running type checking...$(RESET)"
	cd backend && mypy . --ignore-missing-imports
	cd frontend && $(NPM) run type-check
	@echo "$(GREEN)✓ Type checking completed$(RESET)"

# Data Collection Commands
collect:
	@echo "$(BLUE)Running manual data collection...$(RESET)"
	cd backend && $(PYTHON) -c "
import asyncio
from core.source_manager import SourceManager

async def collect():
    manager = SourceManager()
    await manager.initialize_collectors()
    print('Data collection completed')

asyncio.run(collect())
"
	@echo "$(GREEN)✓ Data collection completed$(RESET)"

collect-apis:
	@echo "$(BLUE)Collecting from API sources only...$(RESET)"
	cd backend && $(PYTHON) scripts/collect_api_data.py
	@echo "$(GREEN)✓ API data collection completed$(RESET)"

collect-news:
	@echo "$(BLUE)Collecting from news sources only...$(RESET)"
	cd backend && $(PYTHON) scripts/collect_news_data.py
	@echo "$(GREEN)✓ News data collection completed$(RESET)"

# Docker Commands
docker-build:
	@echo "$(BLUE)Building Docker images...$(RESET)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓ Docker images built$(RESET)"

docker-up:
	@echo "$(BLUE)Starting Docker services...$(RESET)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Docker services started$(RESET)"

docker-down:
	@echo "$(BLUE)Stopping Docker services...$(RESET)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Docker services stopped$(RESET)"

docker-logs:
	@echo "$(BLUE)Viewing Docker logs...$(RESET)"
	$(DOCKER_COMPOSE) logs -f

docker-shell-api:
	@echo "$(BLUE)Opening shell in API container...$(RESET)"
	$(DOCKER_COMPOSE) exec api bash

docker-shell-db:
	@echo "$(BLUE)Opening shell in database container...$(RESET)"
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d colombian_platform

# Production Commands
build: build-backend build-frontend
	@echo "$(GREEN)✓ Production build completed$(RESET)"

build-backend:
	@echo "$(BLUE)Building backend for production...$(RESET)"
	cd backend && $(PYTHON) manage.py collectstatic --noinput
	@echo "$(GREEN)✓ Backend build completed$(RESET)"

build-frontend:
	@echo "$(BLUE)Building frontend for production...$(RESET)"
	cd frontend && $(NPM) run build
	@echo "$(GREEN)✓ Frontend build completed$(RESET)"

deploy:
	@echo "$(BLUE)Deploying to production...$(RESET)"
	# Add your deployment commands here
	@echo "$(YELLOW)⚠ Deployment script not implemented$(RESET)"

backup:
	@echo "$(BLUE)Creating database backup...$(RESET)"
	pg_dump colombian_platform > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Database backup created$(RESET)"

# Maintenance Commands
clean: clean-backend clean-frontend clean-docker
	@echo "$(GREEN)✓ Cleanup completed$(RESET)"

clean-backend:
	@echo "$(BLUE)Cleaning backend temporary files...$(RESET)"
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd backend && find . -type f -name "*.pyo" -delete 2>/dev/null || true
	cd backend && rm -rf .pytest_cache/ 2>/dev/null || true
	cd backend && rm -rf htmlcov/ 2>/dev/null || true
	@echo "$(GREEN)✓ Backend cleanup completed$(RESET)"

clean-frontend:
	@echo "$(BLUE)Cleaning frontend temporary files...$(RESET)"
	cd frontend && rm -rf node_modules/.cache/ 2>/dev/null || true
	cd frontend && rm -rf build/ 2>/dev/null || true
	cd frontend && rm -rf dist/ 2>/dev/null || true
	@echo "$(GREEN)✓ Frontend cleanup completed$(RESET)"

clean-docker:
	@echo "$(BLUE)Cleaning Docker resources...$(RESET)"
	$(DOCKER) system prune -f
	@echo "$(GREEN)✓ Docker cleanup completed$(RESET)"

logs:
	@echo "$(BLUE)Viewing application logs...$(RESET)"
	tail -f backend/logs/app.log

status:
	@echo "$(BLUE)Checking system status...$(RESET)"
	@echo "Backend API:"
	@curl -s http://localhost:8000/health || echo "$(RED)✗ Backend API not responding$(RESET)"
	@echo "\nFrontend:"
	@curl -s http://localhost:3000 > /dev/null && echo "$(GREEN)✓ Frontend running$(RESET)" || echo "$(RED)✗ Frontend not responding$(RESET)"
	@echo "\nDatabase:"
	@pg_isready -h localhost -p 5432 && echo "$(GREEN)✓ Database running$(RESET)" || echo "$(RED)✗ Database not responding$(RESET)"
	@echo "\nRedis:"
	@redis-cli ping > /dev/null 2>&1 && echo "$(GREEN)✓ Redis running$(RESET)" || echo "$(RED)✗ Redis not responding$(RESET)"

# Quick Development Workflows
quick-start: install setup-db dev-services
	@echo "$(GREEN)✓ Quick start completed - run 'make dev-api' and 'make dev-web' in separate terminals$(RESET)"

full-setup: install-dev setup-db seed docker-build
	@echo "$(GREEN)✓ Full development setup completed$(RESET)"

ci-test: lint test-coverage
	@echo "$(GREEN)✓ CI test pipeline completed$(RESET)"

# Data Analysis Commands
analyze-sources:
	@echo "$(BLUE)Analyzing data source performance...$(RESET)"
	cd backend && $(PYTHON) scripts/analyze_sources.py
	@echo "$(GREEN)✓ Source analysis completed$(RESET)"

health-check:
	@echo "$(BLUE)Running comprehensive health check...$(RESET)"
	cd backend && $(PYTHON) scripts/health_check.py
	@echo "$(GREEN)✓ Health check completed$(RESET)"

# Security Commands
security-scan:
	@echo "$(BLUE)Running security scan...$(RESET)"
	cd backend && safety check -r requirements.txt
	cd frontend && $(NPM) audit
	@echo "$(GREEN)✓ Security scan completed$(RESET)"

# Performance Commands
performance-test:
	@echo "$(BLUE)Running performance tests...$(RESET)"
	cd backend && $(PYTEST) tests/test_performance.py -v
	@echo "$(GREEN)✓ Performance tests completed$(RESET)"

load-test:
	@echo "$(BLUE)Running load tests...$(RESET)"
	# Add load testing commands (e.g., with locust)
	@echo "$(YELLOW)⚠ Load testing not implemented$(RESET)"

# Documentation Commands
docs:
	@echo "$(BLUE)Building documentation...$(RESET)"
	cd docs && $(PYTHON) -m mkdocs build
	@echo "$(GREEN)✓ Documentation built$(RESET)"

docs-serve:
	@echo "$(BLUE)Serving documentation...$(RESET)"
	cd docs && $(PYTHON) -m mkdocs serve

# Environment-specific commands
dev-reset: clean docker-down docker-up setup-db seed
	@echo "$(GREEN)✓ Development environment reset$(RESET)"

prod-health:
	@echo "$(BLUE)Checking production health...$(RESET)"
	# Add production health check commands
	@echo "$(YELLOW)⚠ Production health check not implemented$(RESET)"