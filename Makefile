.PHONY: install run test lint format build clean

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -q --tb=short

lint:
	ruff check .

format:
	ruff format .

build:
	docker build -t support-api:local .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
