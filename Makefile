SHELL := /bin/bash
.DEFAULT_GOAL := help

app_src = TimeManagerBackend
tests_src = tests

isort = poetry run isort $(app_src) $(tests_src)
autoflake = poetry run autoflake -r --remove-all-unused-imports $(app_src) $(tests_src)
black = poetry run black $(app_src) $(tests_src)
flake8 = poetry run flake8 $(app_src) $(tests_src)
test = poetry run pytest --cov=$(app_src)

.PHONY: format
format:
	$(isort)
	$(autoflake) -i
	$(black)
	$(flake8)

.PHONY: help
help:
	@echo "Format your code by running 'make format'"
	@echo "Formatting configuration can be found in:"
	@echo "pyproject.toml, setup.cfg"
