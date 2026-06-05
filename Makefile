.PHONY: install test lint clean help

help:
	@echo "ChronosGraph Development Commands:"
	@echo "  make install  - Install development dependencies"
	@echo "  make test     - Run unit tests"
	@echo "  make lint     - Run linter (ruff)"
	@echo "  make clean    - Remove temporary files and databases"

install:
	sudo pip3 install numpy pytest ruff

test:
	pytest test_chronosgraph.py

lint:
	ruff check .

clean:
	rm -f *.db
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .ruff_cache
