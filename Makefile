PYTEST_OPTS := tests

.PHONY: test
test:
	@poetry run pytest $(PYTEST_OPTS)

.PHONY: lint
lint:
	@poetry run ruff check .
	@poetry run mypy ja_law_parser/

.PHONY: format
format:
	@poetry run ruff format .
	@poetry run ruff --fix .

# Generate resource files (`*.rst`) with `members` and `show-inheritance` (excluding `undoc-members`) in `docs/resouces/`.
# More info: https://github.com/sphinx-doc/sphinx/issues/8664
# API doc: https://www.sphinx-doc.org/ja/master/man/sphinx-apidoc.html#envvar-SPHINX_APIDOC_OPTIONS
.PHONY: docs-resources
docs-resources:  ## Generate resource files of API documents
	@rm -rf docs/source/resources/*
	@SPHINX_APIDOC_OPTIONS=members,show-inheritance poetry run sphinx-apidoc -f -o docs/source/resources/ "ja_law_parser"

# This task depends on resource files in `docs/resources/`.
.PHONY: docs  ## Generate HTML API documents
docs: clean
	poetry run make -C docs html

.PHONY: build
build: clean lint test docs
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
	@rm -rf docs/build/*
