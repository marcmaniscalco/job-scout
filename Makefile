.PHONY: sync requirements lint format test precommit build build-JobScoutFunction deploy invoke clean

sync:
	uv sync

# Convenience for local inspection; `sam build` regenerates this itself
# via the build-JobScoutFunction target below, so this isn't required
# before building/deploying.
requirements:
	uv export --no-dev --no-hashes --no-emit-project --format requirements-txt > src/requirements.txt

lint:
	uv run ruff check .

format:
	uv run ruff format .

test:
	uv run pytest

precommit:
	uv run pre-commit run --all-files

build:
	sam build --use-container

# Invoked by `sam build` itself (template.yaml sets CodeUri: . and
# Metadata.BuildMethod: makefile on JobScoutFunction). Runs inside the
# SAM build container, which has Python 3.14 + pip but not uv, so uv
# is installed on the fly. $(ARTIFACTS_DIR) is provided by SAM.
build-JobScoutFunction:
	python3 -m pip install --quiet uv
	python3 -m uv export --no-dev --no-hashes --no-emit-project --format requirements-txt > src/requirements.txt
	python3 -m pip install --no-cache-dir -r src/requirements.txt --target "$(ARTIFACTS_DIR)"
	cp -r src/job_scout "$(ARTIFACTS_DIR)/"

deploy: build
	sam deploy

invoke: build
	sam local invoke JobScoutFunction --event events/sqs_jd_event.json

clean:
	rm -rf .aws-sam .pytest_cache .ruff_cache
