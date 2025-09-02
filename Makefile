.PHONY: deps check-deps

# Regenerate pinned runtime deps from pyproject (single source of truth)
deps:
	uv pip compile pyproject.toml -o requirements.runtime.txt --upgrade

# Fail if requirements.runtime.txt is out-of-date vs pyproject.toml
check-deps:
	@tmp=$$(mktemp) ; \
	uv pip compile pyproject.toml -o $$tmp --upgrade >/dev/null ; \
	if ! diff -u requirements.runtime.txt $$tmp ; then \
	  echo "requirements.runtime.txt is stale. Run 'make deps' and commit." >&2 ; \
	  rm -f $$tmp ; \
	  exit 1 ; \
	fi ; \
	rm -f $$tmp ; \
	echo "Deps OK."
