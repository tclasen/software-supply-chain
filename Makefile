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

