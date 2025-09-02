SHELL := /bin/sh
.ONESHELL:

.PHONY: deps check-deps

deps:
	set -eu
	uv pip compile pyproject.toml -o requirements.runtime.txt --upgrade

check-deps:
	set -eu

	# 1) Ensure the pinned file exists
	if [ ! -f requirements.runtime.txt ]; then
	  echo "requirements.runtime.txt is missing. Run 'make deps' and commit." >&2
	  exit 1
	fi

	# 2) Recompute pins to a temp file
	tmp_raw=$$(mktemp)
	uv pip compile pyproject.toml -o "$$tmp_raw" --upgrade >/dev/null

	# 3) Strip comments and compare
	tmp_cur=$$(mktemp)
	tmp_new=$$(mktemp)
	grep -v '^[[:space:]]*#' requirements.runtime.txt > "$$tmp_cur"
	grep -v '^[[:space:]]*#' "$$tmp_raw" > "$$tmp_new"

	if ! diff -u "$$tmp_cur" "$$tmp_new" ; then
	  echo "requirements.runtime.txt is stale. Run 'make deps' and commit." >&2
	  rm -f "$$tmp_raw" "$$tmp_cur" "$$tmp_new"
	  exit 1
	fi

	rm -f "$$tmp_raw" "$$tmp_cur" "$$tmp_new"
	echo "Deps OK."

