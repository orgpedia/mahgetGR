.DEFAULT_GOAL := help

org_code := mahgetGR

tasks :=  # IMP: Write al the tasks here
tasks := $(foreach t,$(tasks),flow/$t)

DOCS = import/documents/
SRC = import/src
LOGS = import/logs
WEBSITE = import/websites/gr.maharashtra.gov.in


.PHONY: help install import flow export check readme lint format pre-commit $(tasks)

help:
	$(info Please use 'make <target>', where <target> is one of)
	$(info )
	$(info   install           install packages and prepare software environment)
	$(info )
	$(info   fetch_site        fetch the html pages for a date range.)
	$(info   merge_fetch       merge the new fetch(es) with earlier fetches.)
	$(info   link_wayback      link the wayback service to the the new urls.)
	$(info   upload_to_archive upload the downloaded pdfs to archive.org)

	$(info )
	$(info   lint              run the code linters)
	$(info   format            reformat code)
	$(info )
	$(info Check the makefile to know exactly what each target is doing.)
	@echo # dummy command



install: pyproject.toml
	uv venv
	uv sync

install_chromium:
	uv run playwright install chromium

fetch_site:
	uv run python -u import/src/fetch_date_site.py import/websites/gr.maharashtra.gov.in | tee import/logs/fetch_site.log

merge_fetch:
	uv run python -u import/src/merge_fetch.py import/websites/gr.maharashtra.gov.in import/documents/merged_fetch.json  | tee import/logs/merge_fetch.log

link_wayback:
	uv run python -u import/src/link_wayback.py import/documents/merged_fetch.json import/documents/wayback.json | tee import/logs/link_wayback.log 

upload_to_archive:
	uv run python -u import/src/upload_to_archive.py import/documents/merged_fetch.json import/documents/wayback.json import/documents/archive.json import/documents | tee import/logs/upload_to_archive.log


update_archive:
	uv run python -u $(SRC)/update_to_archive.py $(DOCS)/merged_fetch.json $(DOCS)/wayback.json $(DOCS)/archive.json $(DOCS) | tee $(LOGS)/upload_to_archive.log

update_wayback:
	uv run python -u import/src/update_wayback.py $(DOCS)/merged_fetch.json $(DOCS)/wayback.json | tee $(LOGS)/link_wayback.log

export:
	uv run python flow/src/export_info.py import/documents/merged_fetch.json import/documents/wayback.json import/documents/archive.json export/orgpedia_mahgetGR/GRs.json | tee import/logs/export.log

lint:
	uv run ruff import/src flow/src

format:
	uv run ruff --fix . import/src flow/src
	uv run ruff format . import/src flow/src


# Use pre-commit if there are lots of edits,
# https://pre-commit.com/ for instructions
# Also set git hook `pre-commit install`
pre-commit:
	pre-commit run --all-files

