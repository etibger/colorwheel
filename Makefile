.PHONY: clean test all docs-html docs-man docs-pdf release-docs

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
