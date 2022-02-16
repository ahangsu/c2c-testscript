import os
import pytest

from .app import get_approval, get_clear
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
    ctxt.app_id_1st = create_app(
        ctxt.algod_client, ctxt.addr, ctxt.pk, get_approval(), get_clear()
    )
    ctxt.app_addr_1st = logic.get_application_address(ctxt.app_id_1st)
    ctxt.app_id_2nd = create_app(
        ctxt.algod_client, ctxt.addr, ctxt.pk, get_approval(), get_clear()
    )
    ctxt.app_addr_2nd = logic.get_application_address(ctxt.app_id_2nd)
    # prepare contract
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contract.json")
    with open(path) as f:
        jsonContract = f.read()
    ctxt.contract = Contract.from_json(jsonContract)

    sp = ctxt.algod_client.suggested_params()
    ctxt.p1 = PaymentTxn(ctxt.addr, sp, ctxt.app_addr_1st, int(MIN_BALANCE))
    ctxt.p2 = PaymentTxn(ctxt.addr, sp, ctxt.app_addr_2nd, int(MIN_BALANCE))
    ctxt.stxns = [txn.sign(ctxt.pk) for txn in assign_group_id([ctxt.p1, ctxt.p2])]
    txid = ctxt.algod_client.send_transactions(ctxt.stxns)
    wait_for_confirmation(ctxt.algod_client, txid, 2)

    yield ctxt

    # after all the test, do the cleanup
    delete_app(ctxt.algod_client, ctxt.app_id_1st, ctxt.addr, ctxt.pk)
    delete_app(ctxt.algod_client, ctxt.app_id_2nd, ctxt.addr, ctxt.pk)


def test_algod(context: EnvSetupDict):
    print(
        "=> app1 id: {}, app2 id: {}".format(context.app_id_1st, context.app_id_2nd),
        end=" ",
    )
    signer = AccountTransactionSigner(context.pk)
    atc = AtomicTransactionComposer()
    sp = context.algod_client.suggested_params()
    sp.fee = sp.min_fee * 2
    atc.add_method_call(
        context.app_id_1st,
        find_method(context.contract, "callecho"),
        context.addr,
        sp,
        signer,
        method_args=[context.app_id_2nd],
    )
    result = atc.execute(context.algod_client, 4)
    assert len(result.abi_results) == 1
    result = result.abi_results[0]
    assert not result.decode_error
    assert len(result.tx_info["inner-txns"]) == 1
    assert result.tx_info["inner-txns"][0]["logs"] == result.tx_info["logs"]
    print("=> RESULT: {}".format(result.return_value), end=" ")


def test_indexer_validation(context: EnvSetupDict):
    pass
