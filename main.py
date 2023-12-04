

from utils_common import *
from eth_abi import encode

file_path = os.path.abspath(__file__)
file_name = os.path.basename(file_path)
errorSwaps = []

scan = 'https://zksync2-mainnet.zkscan.io'

era_address_zkpep = '0x7D54a311D56957fa3c9a3e397CA9dC6061113ab3'
era_address_weth  = '0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91'
era_address_eth   = '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'
era_address_syncswap_zkpep_weth_lp = '0x76B39F4E0C6d66877f506bdA2041462760A68593'
era_address_zero = '0x0000000000000000000000000000000000000000'

router_address_syncswap = '0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295'
with open(scriptPath+'abi_syncswap_router.json', "r") as file:
    ABI_SYNCSWAP = json.load(file)

def syncswapPepeSwap(key):
    function_name = inspect.stack()[0][3]
    cprint(f'>>> start {function_name}:')
    wait_normal_gas(NORMAL_GAS)

    web3 = Web3(Web3.HTTPProvider(check_rpc('ERA')['rpc']))
    contract_syncswap = web3.eth.contract(address=router_address_syncswap, abi=ABI_SYNCSWAP)

    account = web3.eth.account.from_key(key)
    my_address = account.address
    # cprint(f'my_address = {my_address}')

    amount = check_token_balance(key, check_rpc('ERA')['rpc'], era_address_zkpep)
    approve_token(key, web3, era_address_zkpep, amount, router_address_syncswap, scan, 'ERA', RETRY)

    # // Determine withdraw mode, to withdraw native ETH or wETH on last step.
    # // 0 - vault internal transfer
    # // 1 - withdraw and unwrap to naitve ETH
    # // 2 - withdraw and wrap to wETH
    # tokenIn, to, withdraw mode
    swap_data = encode(
        ["address", "address", "uint8"], 
        [era_address_zkpep, my_address, 1] )
    
    steps = [{
        'pool': era_address_syncswap_zkpep_weth_lp,
        'data': swap_data,
        'callback': era_address_zero, # we don't have a callback
        'callbackData': '0x',
    }]

    paths = [{
        "steps": steps,
        "tokenIn": era_address_zkpep,
        "amountIn": amount,
    }]
    amount_out_min = 0
    deadline = (int(time.time()) + 10000)

    txn = contract_syncswap.functions.swap(paths, amount_out_min, deadline).build_transaction({
        'gasPrice': web3.eth.gas_price,
        'from': my_address,
        'nonce': web3.eth.get_transaction_count(my_address),
    })
    gas = web3.eth.estimate_gas(txn)
    gas_small = round(gas*gas_ratio)
    txn['gas'] = gas_small

    signed_txn = web3.eth.account.sign_transaction(txn, private_key=key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    pritnt_status_tx(function_name, 'ERA', tx_hash, key)

if __name__ == "__main__":
    with open(scriptPath+"keys.txt", "r") as f:
        KEYS_LIST_ERA = [row.strip() for row in f]
    i = 0
    for key in KEYS_LIST_ERA:
        i = i + 1

        web3 = Web3(Web3.HTTPProvider(check_rpc('ERA')['rpc']))
        address = web3.eth.account.from_key(key).address
        cprint(f'{i} wallet: https://explorer.zksync.io/address/'+address, 'magenta')

        syncswapPepeSwap(key)