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
    # Create 2 (same) application, for later construct inner application call
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
        MIN_BALANCE,
    )
    context.payment_2nd_txn = PaymentTxn(
        context.addr,
        context.algod_client.suggested_params(),
        context.app_addr_2nd,
        MIN_BALANCE,
    )
    context.stxns = [
        txn.sign(context.pk)
        for txn in assign_group_id(
            [context.app_call_txn, context.payment_1st_txn, context.payment_2nd_txn]
        )
    ]
    context.txid = context.algod_client.send_transactions(context.stxns)
    result = wait_for_confirmation(context.algod_client, context.txid, 2)
    assert "logs" not in result
    assert len(result["inner-txns"]) == MAX_INNER_CALL_COUNT
    for i in range(MAX_INNER_CALL_COUNT):
        assert len(result["inner-txns"][i]["logs"]) == 1
        substr_log = str(i) + " time(s) called, called by"
        log_decoded = base64.b64decode(result["inner-txns"][i]["logs"][0]).decode(
            "utf-8"
        )
        assert substr_log in log_decoded


def test_indexer_validation(context: EnvSetupDict):
    time.sleep(10)
    var = context.indexer_client.search_transactions_by_address(
        address=context.addr, txid=context.txid
    )
    print(var)
    pass
