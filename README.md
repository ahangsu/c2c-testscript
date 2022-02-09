# C2C testscript

This repo holds the testscript to test contract-to-contract feature over a private network (will adapt and move to betanet for more tests.)

## Develop Setup

This repo requires Python 3.6 or higher. It is recommended to use a Python virtual environment to install required dependencies.

Setup venv (one time):
- `python3 -m venv venv`

Activate venv:
- `. venv/bin/activate` (under zsh/bash)
- `. venv/bin/activate.fish` (if your shell is fish)

Config your sandbox with configuration file `sandbox.dev`:
```shell
export ALGOD_CHANNEL=""
export ALGOD_URL="https://github.com/algorand/go-algorand"
export ALGOD_BRANCH="master"
export ALGOD_SHA=""
export NETWORK=""
export NETWORK_TEMPLATE="images/algod/DevModeNetwork.json"
export NETWORK_BOOTSTRAP_URL=""
export NETWORK_GENESIS_FILE=""
export INDEXER_URL="https://github.com/algorand/indexer"
export INDEXER_BRANCH="algochoi/c2c-playground"
export INDEXER_SHA=""
export INDEXER_DISABLED=""
```

Install dependencies:
- `pip install -r requirement.txt`

Run tests:
- First, start an instance of [sandbox](https://github.com/algorand/sandbox) (Docker required): `sandbox up dev`.
- `TODO`
- When finished, stop the docker with `sandbox down`.

## Candidate C2C tests

- [ ] Zeph's C2C SDK test
- [ ] Ben's AVM 1.1 Demo code
- [ ] `go-algorand` e2e test for c2c featrue
