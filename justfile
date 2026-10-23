# relic-extract — step 2 of scan -> extract -> embed. `just` lists the recipes.

default:
    @just --list --unsorted

# write ~/.arra/relic.toml with the defaults (kept if it exists)
init: build
    target/release/relic-extract init

# relic-scan months -> ~/.relic-extract/<stream>/YYYY-MM.parquet (only what changed)
run *ARGS: build
    target/release/relic-extract run {{ARGS}}

# per stream: months, chunks, distinct texts, newest message
status: build
    target/release/relic-extract status

# every test: the binary's and the Python reference's
test: test-rs
    uv run --with pytest -q pytest -q tests

# build the binary, then put relic-extract in ~/.local/bin
install: build
    mkdir -p ~/.local/bin
    cp target/release/relic-extract ~/.local/bin/relic-extract
    @echo "installed: ~/.local/bin/relic-extract ($(~/.local/bin/relic-extract --version))"

# the Rust binary (target/release/relic-extract), optimised
build:
    PATH=$HOME/.cargo/bin:$PATH cargo build --release --locked

# Rust tests
test-rs:
    PATH=$HOME/.cargo/bin:$PATH cargo test --release --locked

# Rust vs Python parts, every row and column (writes only ~/.relic-extract-parity)
parity STREAM="text": build
    scripts/parity.sh {{STREAM}}

# raw and cleaned cut vs their references, on a frozen source (scripts/verify.sh)
verify: build
    scripts/verify.sh
