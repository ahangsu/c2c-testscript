import base64
import pytest
import time

from .app import get_approval, get_clear
from ..utils import (
    EnvSetupDict,
    get_config_accounts,
    TESTENV_INUSE,
    MAX_CALL_DEPTH,
    MIN_BALANCE,
    create_app,
)
from algosdk.future.transaction import (
    ApplicationCallTxn,
    OnComplete,
    PaymentTxn,
    algod,
    assign_group_id,
    logic,
    wait_for_confirmation,
)
from algosdk.v2client import indexer


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
    # Create application, for later construct inner application call
    ctxt.app_create_txid, ctxt.app_id = create_app(
        ctxt.algod_client,
        ctxt.addr,
        ctxt.pk,
        get_approval(),
        get_clear(),
    )
    ctxt.app_addr = logic.get_application_address(ctxt.app_id)

    yield ctxt

    # No need to cleanup since it call with DeleteApplicationOC


def test_algod(context: EnvSetupDict):
    sp = context.algod_client.suggested_params()
    context.pay_txn = PaymentTxn(
        context.addr, sp, context.app_addr, (MAX_CALL_DEPTH + 1) * MIN_BALANCE
    )
    context.call_txn = ApplicationCallTxn(
        context.addr,
        sp,
        context.app_id,
        OnComplete.DeleteApplicationOC,
        app_args=[MAX_CALL_DEPTH],
    )
    context.call_txn.fee *= MAX_CALL_DEPTH * 3 + 1
    context.stxn = [
        tx.sign(context.pk)
        for tx in assign_group_id([context.pay_txn, context.call_txn])
    ]
    context.txids = [tx.get_txid() for tx in context.stxn]

    context.algod_client.send_transactions(context.stxn)
    context.results = [
        wait_for_confirmation(context.algod_client, txid, 2) for txid in context.txids
    ]
    result = context.results[1]
    context.txid = context.txids[1]

    for level in range(MAX_CALL_DEPTH, -1, -1):
        assert "logs" in result
        assert len(result["logs"]) == 1
        level_compute = int.from_bytes(base64.b64decode(result["logs"][0]), "big")
        assert 2 ** level == level_compute

        if level == 0:
            assert "inner-txns" not in result
            continue

        assert "inner-txns" in result
        # 3 inner txns: create, pay, call
        assert len(result["inner-txns"]) == 3
        result = result["inner-txns"][-1]


def test_indexer_validation(context: EnvSetupDict):
    time.sleep(5)
    full_txn = context.indexer_client.search_transactions_by_address(
        address=context.addr, txid=context.txid
    )

    assert "transactions" in full_txn
    assert len(full_txn["transactions"]) == 1

    txn_result = full_txn["transactions"][0]
    for level in range(MAX_CALL_DEPTH, -1, -1):
        assert "logs" in txn_result
        assert len(txn_result["logs"]) == 1
        level_compute = int.from_bytes(base64.b64decode(txn_result["logs"][0]), "big")
        assert 2 ** level == level_compute

        if level == 0:
            assert "inner-txns" not in txn_result
            continue

        assert "inner-txns" in txn_result
        # 3 inner txns: create, pay, call
        assert len(txn_result["inner-txns"]) == 3
        txn_result = txn_result["inner-txns"][-1]
