set shell := ["bash", "-lc"]

docs:
	uv run mkdocs serve

# Serve the example project demo site
demo:
	uv run python example_project/manage.py runserver

test:
	uv run pytest
