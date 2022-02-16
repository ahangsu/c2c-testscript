import pytest

from .app import get_approval, get_clear
from ..utils import (
    TESTENV_INUSE,
    get_config_accounts,
    create_app,
    delete_app,
    MIN_BALANCE,
)
from algosdk.future.transaction import (
    PaymentTxn,
    algod,
    logic,
    assign_group_id,
    wait_for_confirmation,
)


@pytest.fixture
def setup():
    client = algod.AlgodClient(TESTENV_INUSE.ALGOD_TOKEN, TESTENV_INUSE.ALGOD_ADDRESS)
    addr, pk = get_config_accounts(TESTENV_INUSE)[0]
    app_id_1st = create_app(client, addr, pk, get_approval(), get_clear())
    app_addr_1st = logic.get_application_address(app_id_1st)
    app_id_2nd = create_app(client, addr, pk, get_approval(), get_clear())
    app_addr_2nd = logic.get_application_address(app_id_2nd)

    sp = client.suggested_params()
    p1 = PaymentTxn(addr, sp, app_addr_1st, int(MIN_BALANCE))
    p2 = PaymentTxn(addr, sp, app_addr_2nd, int(MIN_BALANCE))
    stxns = [txn.sign(pk) for txn in assign_group_id([p1, p2])]
    txid = client.send_transactions(stxns)
    wait_for_confirmation(client, txid, 2)

    yield addr, pk

    delete_app(client, app_id_1st, addr, pk)
    delete_app(client, app_id_2nd, addr, pk)
