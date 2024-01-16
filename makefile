.DEFAULT_GOAL := help

org_code := mahgetGR

tasks :=  # IMP: Write al the tasks here
tasks := $(foreach t,$(tasks),flow/$t)


.PHONY: help install import flow export check readme lint format pre-commit $(tasks)

help:
	$(info Please use 'make <target>', where <target> is one of)
	$(info )
	$(info   install           install packages and prepare software environment)
	$(info )
	$(info   fetch_site        fetch the html pages for a date range.
	$(info   merge_fetch       merge the new fetch(es) with earlier fetches.
	$(info   download_pdfs     download the new pdfs.
	$(info   link_wayback      link the wayback service to the the new urls.
	$(info   upload_to_archive upload the downloaded pdfs to archive.org

	$(info )
	$(info   lint              run the code linters)
	$(info   format            reformat code)
	$(info )
	$(info Check the makefile to know exactly what each target is doing.)
	@echo # dummy command

install: pyproject.toml
	poetry install --only=dev
	poetry run playwright install chromium

fetch_site:
	poetry run python import/src/fetch_date_site.py import/websites/gr.maharashtra.gov.in

merge_fetch:
	poetry run python import/src/merge_fetch.py import/websites/gr.maharashtra.gov.in import/documents/merged_fetch.json

download_pdfs:
	poetry run python import/src/download_pdfs.py import/documents/merged_fetch.json import/documents

link_wayback:
	poetry run python import/src/link_wayback.py import/documents/merged_fetch.json import/documents/wayback.json


upload_to_archive:
	poetry run python import/src/upload_to_archive.py import/documents/merged_fetch.json import/documents/pdfs.json import/documents/wayback.json import/documents/archive.json


lint:
	poetry run black -q .
	poetry run ruff .

format:
	poetry run black -q .
	poetry run ruff --fix .

export: format lint check readme
	poetry run op exportpackage export/data export/orgpedia_$(org_code)

# Use pre-commit if there are lots of edits,
# https://pre-commit.com/ for instructions
# Also set git hook `pre-commit install`
pre-commit:
	pre-commit run --all-files

