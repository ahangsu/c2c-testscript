import pytest

from .app import (
    get_fake_random_approval,
    get_random_byte_approval,
    get_slot_machine_approval,
    get_clear,
)
from ..utils import (
    TESTENV_INUSE,
    get_config_accounts,
    create_app,
    delete_app,
    MIN_BALANCE,
    EnvSetupDict,
    find_method,
)
from algosdk.v2client import indexer
from algosdk.abi import Contract
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
)
from algosdk.future.transaction import (
    PaymentTxn,
    StateSchema,
    algod,
    logic,
    assign_group_id,
    wait_for_confirmation,
)

@pytest.fixture(scope="module")
def context():
    ctxt = EnvSetupDict()
    # Setup Algod and Indexer clients
    ctxt.algod_client = algod.AlgodClient(
        TESTENV_INUSE.ALGOD_TOKEN, TESTENV_INUSE.ALGOD_ADDRESS
    )
    ctxt.indexer_client = indexer.IndexerClient(
        TESTENV_INUSE.INDEXER_TOKEN, TESTENV_INUSE.INDEXER_ADDRESS
    )
    # Setup the account to use
    ctxt.addr, ctxt.pk = get_config_accounts(TESTENV_INUSE)[0]
    _, ctxt.fake_random_id = create_app(
        ctxt.algod_client, ctxt.addr, ctxt.pk, get_fake_random_approval(), get_clear(), StateSchema(1, 0)
    )
    _, ctxt.random_byte_id = create_app(
        ctxt.algod_client, ctxt.addr, ctxt.pk, get_random_byte_approval(), get_clear()
    )
    _, ctxt.slot_machine_id = create_app(
        ctxt.algod_client, ctxt.addr, ctxt.pk, get_slot_machine_approval(), get_clear(), StateSchema(0, 3)
    )

    yield

    delete_app(ctxt.algod_client, ctxt.fake_random_id, ctxt.addr, ctxt.pk)
    delete_app(ctxt.algod_client, ctxt.random_byte_id, ctxt.addr, ctxt.pk)
    delete_app(ctxt.algod_client, ctxt.slot_machine_id, ctxt.addr, ctxt.pk)


def test_algod(context: EnvSetupDict):
    pass


def test_indexer(context: EnvSetupDict):
    pass
