import base58 
from solders.keypair import Keypair
 
def get_wallet_from_private_key_bs58(private_key_bs58: str) -> Keypair:
    wallet = Keypair.from_base58_string(private_key_bs58)    
    return wallet