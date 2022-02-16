import base64
from algosdk.kmd import KMDClient
from algosdk.future.transaction import (
    algod,
    StateSchema,
    ApplicationCreateTxn,
    ApplicationDeleteTxn,
    wait_for_confirmation,
)
from .env_config import TestEnvConfig


def get_config_accounts(configPack: TestEnvConfig):
    kmd_client = KMDClient(configPack.KMD_TOKEN, configPack.KMD_ADDRESS)
    wallets = kmd_client.list_wallets()
    wallet_id = None
    for wallet in wallets:
        if wallet["name"] == configPack.KMD_WALLET_NAME:
            wallet_id = wallet["id"]
            break
    if wallet_id is None:
        raise Exception(
            'Wallet not found for name "{}"'.format(configPack.KMD_WALLET_NAME)
        )
    wallet_handle = kmd_client.init_wallet_handle(
        wallet_id, configPack.KMD_WALLET_PASSWORD
    )
    try:
        addresses = kmd_client.list_keys(wallet_handle)
        privateKeys = [
            kmd_client.export_key(wallet_handle, configPack.KMD_WALLET_PASSWORD, addr)
            for addr in addresses
        ]
        accounts = [(addresses[i], privateKeys[i]) for i in range(len(privateKeys))]
    finally:
        kmd_client.release_wallet_handle(wallet_handle)
    return accounts


def create_app(client: algod.AlgodClient, addr: str, pk: str, approval, clear) -> int:
    # Get suggested params from network
    sp = client.suggested_params()

    # Read in approval teal source && compile
    app_result = client.compile(approval)
    app_bytes = base64.b64decode(app_result["result"])

    # Read in clear teal source && compile
    clear_result = client.compile(clear)
    clear_bytes = base64.b64decode(clear_result["result"])

    # We dont need no stinkin storage
    schema = StateSchema(0, 0)

    # Create the transaction
    create_txn = ApplicationCreateTxn(
        addr,
        sp,
        0,
        app_bytes,
        clear_bytes,
        schema,
        schema,
    )

    # Sign it
    signed_txn = create_txn.sign(pk)

    # Ship it
    txid = client.send_transaction(signed_txn)

    # Wait for the result so we can return the app id
    result = wait_for_confirmation(client, txid, 4)

    return result["application-index"]


def delete_app(client: algod.AlgodClient, app_id: int, addr: str, pk: str):
    # Get suggested params from network
    sp = client.suggested_params()

    # Create the transaction
    txn = ApplicationDeleteTxn(addr, sp, app_id)

    # sign it
    signed = txn.sign(pk)

    # Ship it
    txid = client.send_transaction(signed)

    return wait_for_confirmation(client, txid, 4)
