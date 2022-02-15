from algosdk.kmd import KMDClient
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
