PYTHON=python3

# All targets are PHONY

.PHONY: all $(MAKECMDGOALS)

# Formatting and typecheck

format:
	@${PYTHON} -m black avmon/ tests/

format-check:
	@${PYTHON} -m black --check avmon/ tests/

type-check:
	@${PYTHON} -m mypy avmon/ tests/

check: format-check type-check

# Tests

test:
	@${PYTHON} -m pytest

testx:
	@${PYTHON} -m pytest -x

testxs:
	@${PYTHON} -m pytest -x -s

# Git hooks

pre-commit: check

pre-push: pre-commit test

install-git-hooks:
	@printf "make pre-commit" > .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
	@printf "make pre-push" > .git/hooks/pre-push && chmod +x .git/hooks/pre-push
	@echo "git hooks installed"

# Dependencies

install-deps:
	@${PYTHON} -m pip install --user -r requirements.txt

install-deps-dev: install-deps
	@${PYTHON} -m pip install --user -r requirements-dev.txt

# Setup

create-dotenv:
	@[ -f .env ] || printf "POSTGRES_PASSWORD=$$(pwgen 32 1)\n" > .env

dev-setup: install-deps-dev install-git-hooks create-dotenv

# Running locally

run-collector:
	@${PYTHON} -m avmon.collector

run-backend:
	@${PYTHON} -m avmon.backend

run-both:
	@${PYTHON} -m avmon.both

run-frontend:
	@${PYTHON} -m avmon.frontend

run-all:
	@${PYTHON} -m avmon.all

# Running in Docker

docker-up:
	@docker-compose up --build -d

docker-dbs:
	@docker-compose -f docker-compose-dbs.yml up --build -d

docker-down:
	@docker-compose down -v || docker-compose kill

# Documentation

dot:
	@for file in docs/*.dot; do dot -Tsvg "$$file" > "docs/$$(basename "$$file" .dot).svg"; done
