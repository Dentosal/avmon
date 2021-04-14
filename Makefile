PYTHON=python3.8

format:
	@${PYTHON} -m black avmon/ tests/

format-check:
	@${PYTHON} -m black --check avmon/ tests/

type-check:
	@${PYTHON} -m mypy avmon/ tests/

check: format-check type-check

test:
	@${PYTHON} -m pytest

install-deps:
	@${PYTHON} -m pip install --user -r requirements.txt

install-deps-dev: install-deps
	@${PYTHON} -m pip install --user -r requirements-dev.txt

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
