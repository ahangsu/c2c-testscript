import time
import pytest

from .app import (
    get_oro_cobre_approval,
    get_plata_plomo_approval,
    get_clear,
    get_top_level,
)
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
    PaymentTxn,
    algod,
    logic,
    OnComplete,
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
    _, ctxt.plata_plomo_id = create_app(
        ctxt.algod_client,
        ctxt.addr,
        ctxt.pk,
        get_plata_plomo_approval(),
        get_clear(),
    )
    ctxt.plata_plomo_addr = logic.get_application_address(ctxt.plata_plomo_id)
    _, ctxt.oro_cobre_id = create_app(
        ctxt.algod_client, ctxt.addr, ctxt.pk, get_oro_cobre_approval(), get_clear()
    )
    ctxt.oro_cobre_addr = logic.get_application_address(ctxt.oro_cobre_id)
    _, ctxt.top_level_id = create_app(
        ctxt.algod_client, ctxt.addr, ctxt.pk, get_top_level(), get_clear()
    )
    ctxt.top_level_addr = logic.get_application_address(ctxt.top_level_id)

    yield ctxt

    delete_app(ctxt.algod_client, ctxt.plata_plomo_id, ctxt.addr, ctxt.pk)
    delete_app(ctxt.algod_client, ctxt.oro_cobre_id, ctxt.addr, ctxt.pk)
    delete_app(ctxt.algod_client, ctxt.top_level_id, ctxt.addr, ctxt.pk)


def test_algod(context: EnvSetupDict):
    context.app_call_txn = ApplicationCallTxn(
        context.addr,
        context.algod_client.suggested_params(),
        context.top_level_id,
        OnComplete.NoOpOC,
        foreign_apps=[context.plata_plomo_id, context.oro_cobre_id],
    )
    context.app_call_txn.fee *= 100
    context.payment_txn = PaymentTxn(
        context.addr,
        context.algod_client.suggested_params(),
        context.top_level_addr,
        MIN_BALANCE,
    )
    context.payment_plata_plomo_txn = PaymentTxn(
        context.addr,
        context.algod_client.suggested_params(),
        context.plata_plomo_addr,
        MIN_BALANCE * 3,
    )
    context.payment_oro_cobre_txn = PaymentTxn(
        context.addr,
        context.algod_client.suggested_params(),
        context.oro_cobre_addr,
        MIN_BALANCE * 3,
    )
    context.stxns = [
        txn.sign(context.pk)
        for txn in assign_group_id(
            [
                context.payment_txn,
                context.payment_plata_plomo_txn,
                context.payment_oro_cobre_txn,
                context.app_call_txn,
            ]
        )
    ]
    txids = [s.transaction.get_txid() for s in context.stxns]
    context.algod_client.send_transactions(context.stxns)
    results = [wait_for_confirmation(context.algod_client, txid, 4) for txid in txids]
    result = results[-1]
    context.txid = txids[-1]
    assert "inner-txns" in result
    assert len(result["inner-txns"]) == 2
    assert "inner-txns" in result["inner-txns"][0]
    assert "inner-txns" in result["inner-txns"][1]
    assert len(result["inner-txns"][0]["inner-txns"]) == 2
    assert len(result["inner-txns"][1]["inner-txns"]) == 2
    assert "asset-index" in (plata_inner := result["inner-txns"][0]["inner-txns"][0])
    assert "asset-index" in (plomo_inner := result["inner-txns"][0]["inner-txns"][1])
    assert "asset-index" in (oro_inner := result["inner-txns"][1]["inner-txns"][0])
    assert "asset-index" in (cobre_inner := result["inner-txns"][1]["inner-txns"][1])

    assert plata_inner["txn"]["txn"]["apar"]["an"] == "plata"
    assert plomo_inner["txn"]["txn"]["apar"]["an"] == "plomo"
    assert oro_inner["txn"]["txn"]["apar"]["an"] == "oro"
    assert cobre_inner["txn"]["txn"]["apar"]["an"] == "cobre"


def test_indexer(context: EnvSetupDict):
    time.sleep(5)
    full_txn = context.indexer_client.search_transactions_by_address(
        address=context.addr, txid=context.txid
    )
    assert "transactions" in full_txn
    assert len(full_txn["transactions"]) == 1
    full_txn = full_txn["transactions"][0]

    assert "inner-txns" in full_txn
    assert len(full_txn["inner-txns"]) == 2

    assert "inner-txns" in full_txn["inner-txns"][0]
    assert "inner-txns" in full_txn["inner-txns"][1]
    assert len(full_txn["inner-txns"][0]["inner-txns"]) == 2
    assert len(full_txn["inner-txns"][1]["inner-txns"]) == 2

    assert "asset-config-transaction" in (plata_inner := full_txn["inner-txns"][0]["inner-txns"][0])
    assert "asset-config-transaction" in (plomo_inner := full_txn["inner-txns"][0]["inner-txns"][1])
    assert "asset-config-transaction" in (oro_inner := full_txn["inner-txns"][1]["inner-txns"][0])
    assert "asset-config-transaction" in (cobre_inner := full_txn["inner-txns"][1]["inner-txns"][1])

    assert "created-asset-index" in plata_inner
    assert "created-asset-index" in plomo_inner
    assert "created-asset-index" in oro_inner
    assert "created-asset-index" in cobre_inner

    assert plata_inner["created-asset-index"] != 0
    assert plomo_inner["created-asset-index"] != 0
    assert oro_inner["created-asset-index"] != 0
    assert cobre_inner["created-asset-index"] != 0

    assert "asset-id" in (plata_inner_creation := plata_inner["asset-config-transaction"])
    assert "asset-id" in (plomo_inner_creation := plomo_inner["asset-config-transaction"])
    assert "asset-id" in (oro_inner_creation := oro_inner["asset-config-transaction"])
    assert "asset-id" in (cobre_inner_creation := cobre_inner["asset-config-transaction"])

    assert plata_inner_creation["asset-id"] == 0
    assert plomo_inner_creation["asset-id"] == 0
    assert oro_inner_creation["asset-id"] == 0
    assert cobre_inner_creation["asset-id"] == 0

    assert "params" in plata_inner_creation
    assert "params" in plomo_inner_creation
    assert "params" in oro_inner_creation
    assert "params" in cobre_inner_creation

    assert "name" in plata_inner_creation["params"]
    assert "name" in plomo_inner_creation["params"]
    assert "name" in oro_inner_creation["params"]
    assert "name" in cobre_inner_creation["params"]

    assert plata_inner_creation["params"]["name"] == "plata"
    assert plomo_inner_creation["params"]["name"] == "plomo"
    assert oro_inner_creation["params"]["name"] == "oro"
    assert cobre_inner_creation["params"]["name"] == "cobre"
