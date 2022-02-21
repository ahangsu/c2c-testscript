import base64
import pytest
import time

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
from algosdk.future.transaction import (
    ApplicationCallTxn,
    OnComplete,
    PaymentTxn,
    algod,
    logic,
    assign_group_id,
    wait_for_confirmation,
)
from pyteal.config import MAX_GROUP_SIZE

MAX_ONE_ACCT_CREATE_APP_NUM = 10


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
    # One account can only create 10 applications, we need 17 applications
    # need another account
    another_addr, another_pk = get_config_accounts(TESTENV_INUSE)[1]

    # create 17 applications, first 10 applications
    ctxt.created_app_id = [
        create_app(
            ctxt.algod_client,
            ctxt.addr,
            ctxt.pk,
            get_approval(),
            get_clear(),
        )[1]
        for _ in range(MAX_ONE_ACCT_CREATE_APP_NUM)
    ]
    # next 7 applications
    for _ in range(MAX_GROUP_SIZE + 1 - MAX_ONE_ACCT_CREATE_APP_NUM):
        ctxt.created_app_id.append(
            create_app(
                ctxt.algod_client, another_addr, another_pk, get_approval(), get_clear()
            )[1]
        )
    ctxt.created_app_addr = [
        logic.get_application_address(app_id) for app_id in ctxt.created_app_id
    ]

    yield ctxt

    for app_id in ctxt.created_app_id:
        delete_app(ctxt.algod_client, app_id, ctxt.addr, ctxt.pk)


def test_algod(context: EnvSetupDict):
    sp = context.algod_client.suggested_params()
    payment_txn = [
        PaymentTxn(context.addr, sp, app_addr, MIN_BALANCE)
        for app_addr in context.created_app_addr[:-1]
    ]
    stxns = [txn.sign(context.pk) for txn in assign_group_id(payment_txn)]
    context.algod_client.send_transactions(stxns)

    payment_callee_txn = PaymentTxn(
        context.addr, sp, context.created_app_addr[-1], MIN_BALANCE
    ).sign(context.pk)
    context.algod_client.send_transactions([payment_callee_txn])

    call_txns = [
        ApplicationCallTxn(
            context.addr,
            sp,
            context.created_app_id[i],
            OnComplete.NoOpOC,
            app_args=[context.created_app_id[-1]],
            foreign_apps=[context.created_app_id[-1]],
        )
        for i in range(MAX_GROUP_SIZE)
    ]
    for call_txn in call_txns:
        call_txn.fee *= 2

    stxns = [txn.sign(context.pk) for txn in assign_group_id(call_txns)]
    context.call_txids = [s.transaction.get_txid() for s in stxns]

    context.algod_client.send_transactions(stxns)
    context.results = [
        wait_for_confirmation(context.algod_client, txid, 4)
        for txid in context.call_txids
    ]
    for i in range(MAX_GROUP_SIZE):
        result = context.results[i]
        assert "logs" not in result
        assert "inner-txns" in result
        assert len(result["inner-txns"]) == 1
        assert "logs" in result["inner-txns"][0]
        assert len(result["inner-txns"][0]["logs"]) == 1
        log_str = base64.b64decode(result["inner-txns"][0]["logs"][0]).decode("utf-8")
        expected = "called by " + str(context.created_app_id[i])
        assert log_str == expected


def test_indexer_validation(context: EnvSetupDict):
    time.sleep(5)
    for i in range(MAX_GROUP_SIZE):
        result = context.indexer_client.search_transactions_by_address(
            address=context.addr, txid=context.call_txids[i]
        )
        assert "transactions" in result
        assert len(result["transactions"]) == 1

        result = result["transactions"][0]
        assert "logs" not in result
        assert "inner-txns" in result
        assert len(result["inner-txns"]) == 1
        assert "logs" in result["inner-txns"][0]
        assert len(result["inner-txns"][0]["logs"]) == 1
        log_str = base64.b64decode(result["inner-txns"][0]["logs"][0]).decode("utf-8")
        expected = "called by " + str(context.created_app_id[i])
        assert log_str == expected
