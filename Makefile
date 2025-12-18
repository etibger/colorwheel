.PHONY: clean test all

test:
	@echo "Running pytest..."
	@uv run pytest || { echo "Tests failed due to pytest errors." >&2; exit 1; }
	@echo "All tests passed successfully."

all: clean test
	@echo "Performing everything..."

clean:
	@echo "Cleaning caches and generated files..."
	@rm -rfv .cache .pre-commit .precommit_home .pytest_cache colorwheel.log color_wheel_with_legend.png data/tmp.db data/output.json colorwheel_textual.log colorwheel_debug.log
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
