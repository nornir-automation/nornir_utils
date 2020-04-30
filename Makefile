NAME=$(shell basename $(PWD))

PYTHON:=3.7

DOCKER=docker run \
	   --rm -ir \
	   --name $(NAME)-tests \
	   -v $(PWD):/$(NAME) \
	   --rm $(NAME):latest

.PHONY: docker
docker:
	docker build \
	--build-arg PYTHON=$(PYTHON) \
	--build-arg NAME=$(NAME) \
	-t $(NAME):latest \
	-f Dockerfile \
	.

.PHONY: pytest
pytest:
	poetry run pytest --nbval -vs ${ARGS}

.PHONY: black
black:
	poetry run black --check .

.PHONY: pylama
pylama:
	poetry run pylama .

.PHONY: mypy
mypy:
	poetry run mypy .

.PHONY: tests
tests: black pylama mypy pytest
.PHONY: docker-tests

.PHONY:docker-tests
docker-tests: docker
	$(DOCKER) make tests

.PHONY:
jupyter: jupyter
	docker run --name nornir-tests --rm $(NAME):latest jupyter notebook

.PHONY: docs
docs:
	rm -rf docs/api
	mkdir -p docs/api
	pdoc --html -o docs nornir_utils.plugins.inventory
	pdoc nornir_utils.plugins.processors > docs/api/processors.rst
	pdoc nornir_utils.plugins.functions > docs/api/functions.rst
