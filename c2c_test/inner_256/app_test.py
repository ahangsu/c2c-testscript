import base64
import time
import pytest

from c2c_test.utils import MAX_INNER_CALL_COUNT

from .app import get_approval_call, get_approval_echo, get_clear
from ..utils import (
    TESTENV_INUSE,
    get_config_accounts,
    create_app,
    delete_app,
    MIN_BALANCE,
    EnvSetupDict,
)
from algosdk.v2client import indexer
from algosdk.future.transaction import (
    ApplicationCallTxn,
    OnComplete,
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
    # Create 2 applications, for later construct inner application call
    _, ctxt.app_id_1st = create_app(
        ctxt.algod_client,
        ctxt.addr,
        ctxt.pk,
        get_approval_call(),
        get_clear(),
    )
    ctxt.app_addr_1st = logic.get_application_address(ctxt.app_id_1st)
    _, ctxt.app_id_2nd = create_app(
        ctxt.algod_client,
        ctxt.addr,
        ctxt.pk,
        get_approval_echo(),
        get_clear(),
        StateSchema(1, 0),
    )
    ctxt.app_addr_2nd = logic.get_application_address(ctxt.app_id_2nd)

    yield ctxt

    # after all the test, do the cleanup
    delete_app(ctxt.algod_client, ctxt.app_id_1st, ctxt.addr, ctxt.pk)
    delete_app(ctxt.algod_client, ctxt.app_id_2nd, ctxt.addr, ctxt.pk)


def test_algod(context: EnvSetupDict):
    print(
        "=> app1 id: {}, app2 id: {}".format(context.app_id_1st, context.app_id_2nd),
        end=" ",
    )
    context.app_call_txn = ApplicationCallTxn(
        context.addr,
        context.algod_client.suggested_params(),
        context.app_id_1st,
        OnComplete.NoOpOC,
        foreign_apps=[context.app_id_2nd],
    )
    context.app_call_txn.fee *= MAX_INNER_CALL_COUNT + 1
    context.payment_1st_txn = PaymentTxn(
        context.addr,
        context.algod_client.suggested_params(),
        context.app_addr_1st,
        MIN_BALANCE * 2,
    )
    context.stxns = [
        txn.sign(context.pk)
        for txn in assign_group_id([context.payment_1st_txn, context.app_call_txn])
    ]
    txids = [s.transaction.get_txid() for s in context.stxns]
    context.algod_client.send_transactions(context.stxns)
    results = [wait_for_confirmation(context.algod_client, txid, 4) for txid in txids]
    result = results[1]
    context.txid = txids[1]

    assert "logs" not in result
    assert len(result["inner-txns"]) == MAX_INNER_CALL_COUNT
    for i in range(MAX_INNER_CALL_COUNT):
        assert len(result["inner-txns"][i]["logs"]) == 1
        substr_log = str(i) + " time(s) called, called by"
        log_bytes = result["inner-txns"][i]["logs"][0]
        log_decoded = base64.b64decode(log_bytes).decode("utf-8")
        assert substr_log in log_decoded


def test_indexer_validation(context: EnvSetupDict):
    time.sleep(5)
    full_txn = context.indexer_client.search_transactions_by_address(
        address=context.addr, txid=context.txid
    )
    assert "logs" not in full_txn
    assert len(full_txn["transactions"]) == 1
    assert "logs" not in full_txn["transactions"][0]
    assert len(full_txn["transactions"][0]["inner-txns"]) == MAX_INNER_CALL_COUNT
    for i in range(MAX_INNER_CALL_COUNT):
        log_ith_index = full_txn["transactions"][0]["inner-txns"][i]["logs"]
        assert len(log_ith_index) == 1
        log_bytes = log_ith_index[0]
        substr_log = str(i) + " time(s) called, called by"
        log_decoded = base64.b64decode(log_bytes).decode("utf-8")
        assert substr_log in log_decoded
