SHELL := /bin/bash
.DEFAULT_GOAL := install

app_src = TimeManagerBackend

isort = poetry run isort $(app_src) $(tests_src)
autoflake = poetry run autoflake -r --remove-all-unused-imports $(app_src) $(tests_src)
black = poetry run black $(app_src) $(tests_src)
flake8 = poetry run flake8 $(app_src) $(tests_src)

.PHONY: format
format:
	$(isort)
	$(autoflake) -i
	$(black)
	$(flake8)

.PHONY: test
test:
	@bash ./scripts/test.sh

.PHONY: requirements
requirements:
	@poetry export --dev --without-hashes -f requirements.txt > requirements.txt

.PHONY: deploy_initial
deploy_initial:
	@(exec ./scripts/deploy.sh --initial)

.PHONY: deploy_update
deploy_update:
	@(exec ./scripts/deploy.sh)

.PHONY: deploy_reset
deploy_reset:
	@(exec ./scripts/reset_db.sh)
	@make deploy_update

.PHONY: install
install:
	@poetry install
	@poetry update
	@make requirements
