# relic-extract — step 2 of scan -> extract -> embed. `just` lists the recipes.

default:
    @just --list --unsorted

# write ~/.arra/relic.toml with the defaults (kept if it exists)
init:
    uv run relic-extract init

# relic-scan months -> ~/.relic-extract/<stream>/YYYY-MM.parquet (only what changed)
run *ARGS:
    uv run relic-extract run {{ARGS}}

# per stream: months, chunks, distinct texts, newest message
status:
    uv run relic-extract status

# every test
test:
    uv run --with pytest -q pytest -q tests

# put relic-extract on PATH (~/.local/bin), editable
install:
    uv tool install --force --editable .
