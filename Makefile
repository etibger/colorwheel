.PHONY: help clean test all coverage html_coverage docs-html docs-man docs-pdf release-docs

# Show help for available make targets
help:
	@echo "Available make targets:"
	@echo "  help              Show this help message"
	@echo "  clean             Remove caches and generated files"
	@echo "  test              Run pytest"
	@echo "  all               Clean and test (clean + test)"
	@echo "  coverage          Run pytest with coverage report"
	@echo "  html_coverage     Run pytest with HTML coverage report"
	@echo "  docs-html         Build HTML documentation via Sphinx"
	@echo "  docs-man          Build man pages via Sphinx"
	@echo "  docs-pdf          Build PDF documentation via Sphinx via LaTeX"
	@echo "  release-docs      Copy built HTML docs to docs/released/html"
	@echo "  regenerate-golden Regenerating golden files from data/golden.ods"

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
	@rm -rfv .cache .pre-commit .precommit_home .pytest_cache colorwheel.log color_wheel_with_legend.png data/tmp.db data/output.json colorwheel_textual.log colorwheel_debug.log ./htmlcov docs/_build/html docs/_build/man docs/_build/latex
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

docs-html:
	@echo "Building HTML docs..."
	@uv run sphinx-build -b html docs/source docs/_build/html

docs-man:
	@echo "Building man pages..."
	@uv run sphinx-build -b man docs/source docs/_build/man

docs-pdf:
	@echo "Building PDF docs via LaTeX..."
	@uv run sphinx-build -b latex docs/source docs/_build/latex && \
	@pdflatex -output-directory=docs/_build/latex docs/_build/latex/colorwheel.tex && \
	@mkdir -p docs/_build/pdf && \
	@mv docs/_build/latex/colorwheel.pdf docs/_build/pdf/colorwheel.pdf

release-docs: docs-html
	@echo "Copying built HTML docs to docs/released/html"
	@rsync -a --delete --exclude='.doctrees' docs/_build/html/ docs/released/html/
	@rm -rf docs/released/html/.doctrees

## Regenerate golden reference files from the ODS source
regenerate-golden:
	@echo "Regenerating golden files from data/golden.ods"
	@uv run apps/main.py --data-file data/golden.ods --db-url sqlite:///data/golden.db
	@uv run apps/main.py --data-file data/golden.ods --export-json data/golden.json
	@uv run apps/main.py --data-file data/golden.ods --use-data -o data/golden.png
	@echo "Golden files regenerated: data/golden.db, data/golden.json, data/golden.png"
