.PHONY: clean test all

test:
	@echo "Running pytest..."
	@uv run pytest || { echo "Tests failed due to pytest errors." >&2; exit 1; }
	@echo "All tests passed successfully."

all: clean test
	@echo "Performing everything..."

coverage:
	@echo "Running pytest with coverage..."
	@uv run pytest --cov=. --cov-report=term-missing tests || { echo "Coverage run failed." >&2; exit 1; }

html_coverage:
	@echo "Running pytest with html coverage..."
	@uv run pytest --cov=. --cov-report=html tests || { echo "Coverage run failed." >&2; exit 1; }

clean:
	@echo "Cleaning caches and generated files..."
	@rm -rfv .cache .pre-commit .precommit_home .pytest_cache colorwheel.log color_wheel_with_legend.png data/tmp.db data/output.json colorwheel_textual.log colorwheel_debug.log ./htmlcov
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
