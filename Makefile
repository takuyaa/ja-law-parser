.PHONY: test
test:
	@poetry run pytest tests

.PHONY: lint
lint:
	@poetry run ruff check .
	@poetry run mypy ja_law_parser/

.PHONY: format
format:
	@poetry run ruff format .
	@poetry run ruff --fix .

.PHONY: build
build: clean
	@poetry build

.PHONY: publish
publish: build
	@poetry publish

.PHONY: publish-testpypi
publish-testpypi: build
	@poetry publish -r testpypi

.PHONY: clean
clean:
	@rm -rf dist/
