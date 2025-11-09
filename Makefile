# Makefile for Rudder Encoder Project
#
# Common development tasks using Poetry

.PHONY: help install test lint format type-check validate generate clean dev-setup

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	poetry install

dev-setup: install ## Set up development environment
	poetry run pre-commit install || echo "pre-commit not available"

test: ## Run tests
	poetry run pytest tests/ -v

test-coverage: ## Run tests with coverage
	poetry run pytest tests/ --cov=src --cov-report=html --cov-report=term

lint: ## Run linting
	poetry run flake8 src/ tests/
	poetry run black --check src/ tests/

format: ## Format code
	poetry run black src/ tests/

type-check: ## Run type checking
	poetry run mypy src/

validate: ## Validate default encoder design
	poetry run python src/encoder_generator.py --validate --info

generate: ## Generate default encoder disk
	poetry run python src/encoder_generator.py --output output/default_encoder.scad

generate-all: ## Generate all configurations
	poetry run python src/encoder_generator.py --config default --output output/default_encoder.scad
	poetry run python src/encoder_generator.py --config high_res --output output/high_res_encoder.scad
	poetry run python src/encoder_generator.py --config compact --output output/compact_encoder.scad

export-data: ## Export pattern data
	poetry run python src/encoder_generator.py --export-data output/encoder_patterns.json

optimize: ## Run genetic algorithm optimization
	poetry run python src/genetic_optimizer.py

optimize-high-res: ## Optimize for high resolution
	poetry run python src/genetic_optimizer.py high_res

optimize-compact: ## Optimize for compact size
	poetry run python src/genetic_optimizer.py compact

apply-optimization: ## Apply optimized parameters to default config
	poetry run python src/apply_optimization.py

optimize-and-apply: optimize apply-optimization ## Run optimization and apply results
	@echo "🎯 Optimization complete and applied!"

gui: ## Launch the PyQt GUI controller
	@echo "🖥️ Launching GUI controller..."
	poetry run python src/gui_encoder_controller.py

clean: ## Clean generated files
	rm -rf output/*.scad
	rm -rf output/*.json
	rm -rf output/*.stl
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

all: check-all test validate generate-all ## Complete build and validation pipeline
	@echo "🎉 Complete build pipeline finished successfully!"

check-all: lint type-check ## Run all quality checks

ci: check-all ## Run CI pipeline locally

# Development shortcuts
run-default: ## Quick run with default config
	poetry run python src/encoder_generator.py

run-validate: ## Quick validation run
	poetry run python src/encoder_generator.py --validate --info --verbose

run-high-res: ## Generate high resolution encoder
	poetry run python src/encoder_generator.py --config high_res --output output/high_res_encoder.scad --verbose

run-compact: ## Generate compact encoder
	poetry run python src/encoder_generator.py --config compact --output output/compact_encoder.scad --verbose
