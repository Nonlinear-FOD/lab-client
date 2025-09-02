
.PHONY: deps check-deps

deps:
	uv pip compile pyproject.toml -o requirements.runtime.txt --upgrade

check-deps:
	@if [ ! -f requirements.runtime.txt ]; then \
	  echo "requirements.runtime.txt is missing. Run 'make deps' and commit." >&2 ; \
	  exit 1 ; \
	fi
	@tmp=$$(mktemp) ; \
	uv pip compile pyproject.toml -o $$tmp --upgrade >/dev/null ; \
	if ! diff -u requirements.runtime.txt $$tmp ; then \
	  echo "requirements.runtime.txt is stale. Run 'make deps' and commit." >&2 ; \
	  rm -f $$tmp ; \
	  exit 1 ; \
	fi ; \
	rm -f $$tmp ; \
	echo "Deps OK."
