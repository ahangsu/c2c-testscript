import pytest

from .app import get_approval, get_clear
from ..utils import (
    TESTENV_INUSE,
    get_config_accounts,
    create_app,
    delete_app,
    MIN_BALANCE,
    EnvSetupDict,
)
from algosdk.v2client import indexer
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.future.transaction import (
    PaymentTxn,
    algod,
    logic,
    assign_group_id,
    wait_for_confirmation,
)


@pytest.fixture
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
    # Create 2 (same) application, for later construct inner application call
    ctxt.app_id_1st = create_app(
        ctxt.algod_client, ctxt.addr, ctxt.pk, get_approval(), get_clear()
    )
    ctxt.app_addr_1st = logic.get_application_address(ctxt.app_id_1st)
    ctxt.app_id_2nd = create_app(
        ctxt.algod_client, ctxt.addr, ctxt.pk, get_approval(), get_clear()
    )
    ctxt.app_addr_2nd = logic.get_application_address(ctxt.app_id_2nd)

    ctxt.sp = ctxt.algod_client.suggested_params()
    ctxt.p1 = PaymentTxn(ctxt.addr, ctxt.sp, ctxt.app_addr_1st, int(MIN_BALANCE))
    ctxt.p2 = PaymentTxn(ctxt.addr, ctxt.sp, ctxt.app_addr_2nd, int(MIN_BALANCE))
    ctxt.stxns = [txn.sign(ctxt.pk) for txn in assign_group_id([ctxt.p1, ctxt.p2])]
    txid = ctxt.algod_client.send_transactions(ctxt.stxns)
    wait_for_confirmation(ctxt.algod_client, txid, 2)
    ctxt.signer = AccountTransactionSigner(ctxt.pk)

    yield ctxt

    # after all the test, do the cleanup
    delete_app(ctxt.algod_client, ctxt.app_id_1st, ctxt.addr, ctxt.pk)
    delete_app(ctxt.algod_client, ctxt.app_id_2nd, ctxt.addr, ctxt.pk)


def test_algod(context: EnvSetupDict):
    print(context.app_id_1st, context.app_id_2nd)
    pass


def test_indexer_validation(context: EnvSetupDict):
    pass
