from dataclasses import dataclass


@dataclass
class TestEnvConfig:
    ALGOD_ADDRESS: str
    ALGOD_TOKEN: str
    KMD_ADDRESS: str
    KMD_TOKEN: str
    KMD_WALLET_NAME: str
    KMD_WALLET_PASSWORD: str
    INDEXER_TOKEN: str
    INDEXER_ADDRESS: str


SandBoxTestEnvConfig = TestEnvConfig(
    ALGOD_ADDRESS="http://localhost:4001",
    ALGOD_TOKEN="a" * 64,
    KMD_ADDRESS="http://localhost:4002",
    KMD_TOKEN="a" * 64,
    KMD_WALLET_NAME="unencrypted-default-wallet",
    KMD_WALLET_PASSWORD="",
    INDEXER_TOKEN="",
    INDEXER_ADDRESS="http://localhost:8980",
)

TESTENV_INUSE = SandBoxTestEnvConfig

MIN_BALANCE = int(1e5)

MAX_INNER_CALL_COUNT = 256

MAX_CALL_DEPTH = 8

# TODO needs configuration for betanet, but we now work over sandbox settings
# NOTE some thoughts about how this is done for general betanet / any other networks
