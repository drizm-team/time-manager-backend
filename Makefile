SHELL := /bin/bash
.DEFAULT_GOAL := install

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

.PHONY: requirements
requirements:
	@poetry export --dev --without-hashes -f requirements.txt > requirements.txt

.PHONY: deploy_start
deploy_start:
	@(exec ./scripts/deploy.sh)

.PHONY: deploy_reset
deploy_reset:
	@(exec ./scripts/reset_db.sh)

.PHONY: install
install:
	@poetry install
