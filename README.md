# C2C testscript

This repo holds the testscript to test contract-to-contract feature over a private network (will adapt and move to betanet for more tests.)

## Develop Setup

This repo requires Python 3.6 or higher. It is recommended to use a Python virtual environment to install required dependencies.

Setup venv (one time):
- `python3 -m venv .venv`

Activate venv:
- `. .venv/bin/activate` (under zsh/bash)
- `. .venv/bin/activate.fish` (if your shell is fish)

Install dependencies:
- `pip install -r requirements.txt`

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
export INDEXER_BRANCH="develop"
export INDEXER_SHA=""
export INDEXER_DISABLED=""
```

Run tests:
- First, start an instance of [sandbox](https://github.com/algorand/sandbox) (Docker required): `sandbox up dev`.
- Test with `pytest c2c_test -v -s` (`-v` gives verbose look on each sub-test, `-s` allows stdout print log).
- When finished, stop the docker with `sandbox down` (and `sandbox clean`).

## About Using Betanet Dispenser

> Time: 2020/02/10 11:00

I took notes about what I did for taking (enough?) fund to test over betanet, and leave room for discussion about how much fund needed.

Essentially create wallet and account first:

```shell
# ~/node/betanetdata is where my betanet-data sits
goal node start -d ~/node/betanetdata/
# catchup (16160000... checkpoint is for 3.3.0beta, need to update later)
goal node catchup 16160000#FHLQUKMAUPW5GI5KTLLDDSXIZXT6UTEAYGSU6CVPI7LOOX4WXNYA -d ~/node/betanetdata/
# open a new wallet for betanet test
goal wallet new betanet-test -d ~/node/betanetdata/
# open a new account for betanet test
goal account new tester -d ~/node/betanetdata/
```

Then go to [dispenser](https://betanet.algoexplorer.io/dispenser) to retrieve some fund to initiate the test.

Transaction ID: [NT3XPWO2NFDKCJTMUATNH2H5HGB47XPDTOR4SDLHFMZTNRIMLMUA](https://betanet.algoexplorer.io/tx/NT3XPWO2NFDKCJTMUATNH2H5HGB47XPDTOR4SDLHFMZTNRIMLMUA).

> Can also verify with `goal account list -d ~/node/betanetdata** to check how much microAlgos we have.

**TODO**: The question left to be answered is: 
- if we can provide a unified url+port flavor solution so we can quickly adapt from sandbox test to betanet test.

## Candidate C2C tests

- [ ] Zeph's C2C SDK test (need to change pre-compute app-id to something else)
- [ ] Ben's AVM 1.1 Demo code
- [ ] `go-algorand` e2e test for c2c featrue `app-inner-calls.py`

### On the possibility of running such tests

There are 2 things I am thinking that might stop a test from being executed over betanet:
- Too much fund needed (100+?)
- Relying on a pre-computed applicationID and impossible to rewrite

Need to think through contract code, check how much fund needed, and decide if the sum of all these funds are lower than a small number of dispense.
