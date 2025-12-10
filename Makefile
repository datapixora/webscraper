.PHONY: help build up down restart logs clean test backend-shell frontend-shell db-shell redis-shell migrate seed install install-backend install-frontend format lint

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)WebScraper Platform - Development Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Operations

build: ## Build all Docker containers
	@echo "$(BLUE)Building Docker containers...$(NC)"
	docker-compose build

up: ## Start all services
	@echo "$(GREEN)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - API Docs: http://localhost:8000/docs"
	@echo "  - Flower: http://localhost:5555"

down: ## Stop all services
	@echo "$(YELLOW)Stopping all services...$(NC)"
	docker-compose down

restart: ## Restart all services
	@echo "$(YELLOW)Restarting all services...$(NC)"
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-worker: ## Show worker logs
	docker-compose logs -f worker

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

clean: ## Remove all containers, volumes, and images
	@echo "$(RED)Removing all containers, volumes, and images...$(NC)"
	docker-compose down -v --rmi all
	@echo "$(GREEN)Cleanup complete!$(NC)"

##@ Development

install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend dependencies
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	cd backend && pip install -r requirements.txt && pip install -r requirements-dev.txt

install-frontend: ## Install frontend dependencies
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd frontend && npm install

dev: ## Start development environment (with logs)
	@echo "$(GREEN)Starting development environment...$(NC)"
	docker-compose up

dev-bg: up ## Start development environment in background
	@echo "$(GREEN)Development environment running in background$(NC)"

##@ Database

migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	docker-compose exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MESSAGE="your message")
	@echo "$(BLUE)Creating new migration...$(NC)"
	docker-compose exec backend alembic revision --autogenerate -m "$(MESSAGE)"

migrate-downgrade: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	docker-compose exec backend alembic downgrade -1

db-reset: ## Reset database (drop and recreate)
	@echo "$(RED)Resetting database...$(NC)"
	docker-compose down postgres
	docker volume rm webscraper_postgres_data || true
	docker-compose up -d postgres
	@sleep 5
	@make migrate
	@make seed

seed: ## Seed database with sample data
	@echo "$(BLUE)Seeding database...$(NC)"
	docker-compose exec backend python scripts/seed_data.py

##@ Shell Access

backend-shell: ## Access backend container shell
	docker-compose exec backend /bin/bash

worker-shell: ## Access worker container shell
	docker-compose exec worker /bin/bash

frontend-shell: ## Access frontend container shell
	docker-compose exec frontend /bin/sh

db-shell: ## Access PostgreSQL shell
	docker-compose exec postgres psql -U webscraper -d webscraper_db

redis-shell: ## Access Redis CLI
	docker-compose exec redis redis-cli

##@ Testing

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@make test-backend
	@make test-frontend

test-backend: ## Run backend tests
	@echo "$(BLUE)Running backend tests...$(NC)"
	docker-compose exec backend pytest tests/ -v

test-backend-cov: ## Run backend tests with coverage
	@echo "$(BLUE)Running backend tests with coverage...$(NC)"
	docker-compose exec backend pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-frontend: ## Run frontend tests
	@echo "$(BLUE)Running frontend tests...$(NC)"
	docker-compose exec frontend npm test

test-frontend-e2e: ## Run frontend E2E tests
	@echo "$(BLUE)Running frontend E2E tests...$(NC)"
	docker-compose exec frontend npm run test:e2e

##@ Code Quality

format: ## Format code (Python & TypeScript)
	@echo "$(BLUE)Formatting code...$(NC)"
	docker-compose exec backend black app/ tests/
	docker-compose exec backend isort app/ tests/
	docker-compose exec frontend npm run format

lint: ## Lint code (Python & TypeScript)
	@echo "$(BLUE)Linting code...$(NC)"
	docker-compose exec backend flake8 app/ tests/
	docker-compose exec backend mypy app/
	docker-compose exec frontend npm run lint

lint-fix: ## Fix linting issues
	@echo "$(BLUE)Fixing linting issues...$(NC)"
	docker-compose exec backend black app/ tests/
	docker-compose exec backend isort app/ tests/
	docker-compose exec frontend npm run lint:fix

##@ Monitoring

ps: ## Show running containers
	docker-compose ps

stats: ## Show container resource usage
	docker stats

flower: ## Open Flower monitoring (Celery)
	@echo "$(GREEN)Opening Flower at http://localhost:5555$(NC)"
	@open http://localhost:5555 || xdg-open http://localhost:5555 || start http://localhost:5555

##@ Production

build-prod: ## Build production images
	@echo "$(BLUE)Building production images...$(NC)"
	docker-compose -f docker-compose.prod.yml build

up-prod: ## Start production environment
	@echo "$(GREEN)Starting production environment...$(NC)"
	docker-compose -f docker-compose.prod.yml up -d

down-prod: ## Stop production environment
	@echo "$(YELLOW)Stopping production environment...$(NC)"
	docker-compose -f docker-compose.prod.yml down

##@ Utilities

check-env: ## Check if .env file exists
	@if [ ! -f .env ]; then \
		echo "$(RED).env file not found!$(NC)"; \
		echo "$(YELLOW)Copy .env.example to .env and update values$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN).env file exists$(NC)"; \
	fi

create-env: ## Create .env from .env.example
	@if [ -f .env ]; then \
		echo "$(YELLOW).env file already exists!$(NC)"; \
	else \
		cp .env.example .env; \
		echo "$(GREEN).env file created from .env.example$(NC)"; \
		echo "$(YELLOW)Please update .env with your values$(NC)"; \
	fi

api-docs: ## Open API documentation
	@echo "$(GREEN)Opening API docs at http://localhost:8000/docs$(NC)"
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || start http://localhost:8000/docs

backup-db: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	docker-compose exec -T postgres pg_dump -U webscraper webscraper_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Database backup created$(NC)"

restore-db: ## Restore database (usage: make restore-db FILE=backup.sql)
	@echo "$(BLUE)Restoring database from $(FILE)...$(NC)"
	docker-compose exec -T postgres psql -U webscraper -d webscraper_db < $(FILE)
	@echo "$(GREEN)Database restored$(NC)"

playwright-install: ## Install Playwright browsers
	@echo "$(BLUE)Installing Playwright browsers...$(NC)"
	docker-compose exec backend playwright install

init: create-env build up migrate seed ## Initialize project from scratch
	@echo "$(GREEN)Project initialized successfully!$(NC)"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - API Docs: http://localhost:8000/docs"
