.PHONY: all
all:| fix format ci

.PHONY: ci
ci:| lint check test

.PHONY: fix
fix: install
	uv run ruff check --fix-only .

.PHONY: format
format: install
	uv run ruff format .

.PHONY: lint
lint: install
	uv run ruff check .

.PHONY: check
check: install
	uv run mypy .

.PHONY: test
test: install
	uv run pytest

.PHONY: install
install:
	uv sync --all-packages

.PHONY: clean
clean:
	git clean -dfX

.PHONY: download
download:
	uv run src/software_supply_chain/download_pypi.py

.PHONY: serve
serve:
	uv run uvicorn --host=0.0.0.0 --port=8000 --root-path=src --reload software_supply_chain.web:app

.PHONY: datasette
datasette:
	uv run datasette pypi.db