import requests
import random
from termcolor import cprint
import time
import os
import json
from decimal import Decimal
from web3 import Web3
from loguru import logger
from tqdm import tqdm
from utils_config import *
import inspect

print(os.path.dirname(os.path.realpath(__file__)))
scriptPath = os.path.dirname(os.path.realpath(__file__))+"/"

log_folder = scriptPath+'log'
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

with open(scriptPath+"abi_erc20.json", "r") as file:
    ERC20_ABI = json.load(file)

def token_to_wei(token_amount, decimal_factor):
    return int(token_amount * 10**decimal_factor)

def token_from_wei(token_amount, decimal_factor):
    if (token_amount == 0):
        return 0
    return round(Decimal(token_amount / 10**decimal_factor), 8)

def intToDecimal(qty, decimal):
    return int(qty * int("".join(["1"] + ["0"]*decimal)))

def decimalToInt(qty, decimal):
    return qty/ int("".join((["1"]+ ["0"]*decimal)))

def sleepForAWhile(min,max,log=True):
    sleepT=random.randint(min,max)
    if (log):
        cprint(f">>> sleep  time = {sleepT}")
    time.sleep(sleepT)

def sleeping(from_sleep, to_sleep):
    x = random.randint(from_sleep, to_sleep)
    for i in tqdm(range(x), desc='sleep ', bar_format='{desc}: {n_fmt}/{total_fmt}'):
        time.sleep(1)

def prices():
    currency_price = []
    response = requests.get(url=f'https://api.gateio.ws/api/v4/spot/tickers')
    currency_price.append(response.json())
    return currency_price

RPCS = [
    {'chain': 'ETH',        'chain_id': 1,      'rpc': 'https://rpc.ankr.com/eth',         'scan': 'https://etherscan.io',                'token': 'ETH'},
    {'chain': 'ERA',        'chain_id': 324,    'rpc': 'https://rpc.ankr.com/zksync_era',  'scan': 'https://www.oklink.com/zksync',   'token': 'ETH'},
    {'chain': 'ARBITRUM',   'chain_id': 42161,  'rpc': 'https://arb1.arbitrum.io/rpc',     'scan': 'https://arbiscan.io',                 'token': 'ETH'},
]

STABLE_CONTRACTS_ETH = {'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7'}
STABLE_CONTRACTS_AVAXC = {'USDC': '0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E', 'USDT': '0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7'}
STABLE_CONTRACTS_MATIC = {'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', 'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F'}
STABLE_CONTRACTS_ARBITRUM = {'USDC': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8', 'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9'}
STABLE_CONTRACTS_OPTIMISM = {'USDC': '0x7F5c764cBc14f9669B88837ca1490cCa17c31607', 'USDT': ''}
STABLE_CONTRACTS_FTM = {'USDC': '0x04068DA6C83AFCFA0e13ba15A6696662335D5B75', 'USDT': ''}

STABLE_CONTRACTS = {
    'ETH': STABLE_CONTRACTS_ETH,
    'AVAXC': STABLE_CONTRACTS_AVAXC,
    'MATIC': STABLE_CONTRACTS_MATIC,
    'ARBITRUM': STABLE_CONTRACTS_ARBITRUM,
    'OPTIMISM': STABLE_CONTRACTS_OPTIMISM,
    'FTM': STABLE_CONTRACTS_FTM }


def check_rpc(chain):
    for elem in RPCS:
        if elem['chain'] == chain:
            RPC = elem['rpc']
            chainId = elem['chain_id']
            scan = elem['scan']
            token = elem['token']

            return {
                'rpc': RPC, 'chain_id': chainId, 'scan': scan, 'token': token
            }
        
def check_balance(privatekey, rpc_chain, symbol_chain):
    try:
            
        web3 = Web3(Web3.HTTPProvider(rpc_chain))
        account = web3.eth.account.from_key(privatekey)
        balance = web3.eth.get_balance(web3.to_checksum_address(account.address))
        humanReadable = web3.from_wei(balance,'ether')

        try:
            currency_price = prices()
            for currency in currency_price[0]:
                if currency['currency_pair'] == f'{symbol_chain}_USDT':
                    price = Decimal(currency['last'])
        except: 
            price = 300

        gas = web3.eth.gas_price
        gasPrice = decimalToInt(gas, 18)

        balance = round(Decimal(humanReadable), 8)
        balance_in_usdt = round(Decimal(Decimal(humanReadable)*Decimal(price)), 6)
        # if (balance > 0):
            # cprint(f'balance: {balance} {symbol_chain}; {balance_in_usdt} USDT')
        return balance, balance_in_usdt


    except Exception as error:
        cprint(f'error : {error}', 'yellow')
        0, 0

def check_token_balance(privatekey, rpc_chain, address_contract):
    try:

        web3 = Web3(Web3.HTTPProvider(rpc_chain))
        account = web3.eth.account.from_key(privatekey)
        wallet = account.address
        token_contract = web3.eth.contract(address=web3.to_checksum_address(address_contract), abi=ERC20_ABI) 
        token_balance = token_contract.functions.balanceOf(web3.to_checksum_address(wallet)).call()

        symbol = token_contract.functions.symbol().call()
        token_decimal = token_contract.functions.decimals().call()
        humanReadable = decimalToInt(token_balance, token_decimal) 

        # cprint(f'balance : {token_balance} {symbol}, {token_decimal} decimals', 'white')
        # cprint(f'balance for Human: {humanReadable} {symbol}', 'white')

        return token_balance

    except Exception as error:
        cprint(f'error : {error}', 'yellow')
        return 0

def getChainsWithNativeTokenBalance(privatekey, chain_list):
    result = []
    for chain in chain_list:
        data = check_rpc(chain)
        rpc_chain = data['rpc']
        symbol_chain = data['token']
        cprint(f'{chain} balance:','green')
        balance, balance_in_usdt  = check_balance(privatekey, rpc_chain, symbol_chain)
        if (balance > 0):
            result.append(chain)
    return result

def generateNewRandomList(KEYS_LIST, ratio):
    if (ratio >= 1) :
        return KEYS_LIST
     
    size = int(len(KEYS_LIST) * ratio)
    # Create a new list with a random selection of items from KEYS_LIST
    new_list = random.sample(KEYS_LIST, size)
    return new_list

def getFeePerGas(SRC_CHAIN, web3):
    if (SRC_CHAIN == 'ERA'):                                                           maxPriorityFeePerGas = web3.to_wei('0.25', 'gwei')
    else:                                                                              maxPriorityFeePerGas = web3.eth.max_priority_fee
    
    if (SRC_CHAIN == 'AVAXC'):                                                         maxPriorityFeePerGas = web3.to_wei('1.5', 'gwei')
    if (SRC_CHAIN == 'ARBITRUM'):                                                      maxPriorityFeePerGas = web3.to_wei('0', 'gwei')
    if (SRC_CHAIN == 'MATIC' and maxPriorityFeePerGas < web3.to_wei('30', 'gwei')):    maxPriorityFeePerGas = web3.to_wei('31', 'gwei')
    
        
    maxFeePerGas = web3.eth.gas_price + maxPriorityFeePerGas
    if (SRC_CHAIN == 'ERA'):      maxFeePerGas = web3.eth.gas_price
    if (SRC_CHAIN == 'AVAXC'):    maxFeePerGas = web3.eth.gas_price + web3.to_wei('10', 'gwei')
    if (SRC_CHAIN == 'ARBITRUM'): maxFeePerGas = web3.eth.gas_price + web3.to_wei('0.035', 'gwei')
    if (SRC_CHAIN == 'MATIC'):    maxFeePerGas = web3.eth.gas_price + web3.to_wei('200', 'gwei')

    # print(f"maxPriorityFeePerGas: {maxPriorityFeePerGas}")
    # print(f"maxFeePerGas: {maxFeePerGas}")

    return maxPriorityFeePerGas, maxFeePerGas

def check_allowance(chain, token_address, wallet, spender):

    try:
        data = check_rpc(chain)
        rpc_chain = data['rpc']
        web3 = Web3(Web3.HTTPProvider(rpc_chain))
        contract  = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
        amount_approved = contract.functions.allowance(wallet, spender).call()
        return amount_approved
    except Exception as error:
        cprint(f'>>> check_allowance: {error}', 'red')



def approve_token(private_key, web3: Web3, address_contract, amount_wei, router_address, scan, SRC_CHAIN, retry = 0):
    function_name = inspect.stack()[0][3]
    cprint(f'>>> start {function_name}:')

    try:

        my_address = web3.eth.account.from_key(private_key).address
        allowance_amount = check_allowance(SRC_CHAIN, address_contract, my_address, router_address)

        if amount_wei > allowance_amount:
            number = random.randint(2000000000000000000000000000000, 5000000000000000000000000000000000000)

            if (number < amount_wei):
                number = amount_wei

            token_contract = web3.eth.contract(address=address_contract, abi=ERC20_ABI)
            approve_tx = token_contract.functions.approve(router_address, number).build_transaction({
                'from': web3.eth.account.from_key(private_key).address,
                'nonce': web3.eth.get_transaction_count(my_address),
                'gasPrice': web3.eth.gas_price
            })
            gas = web3.eth.estimate_gas(approve_tx)
            gas_small = round(gas*gas_approve_ratio)
            approve_tx['gas'] = gas_small

            signed_tx = web3.eth.account.sign_transaction(approve_tx, private_key=private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

            result = pritnt_status_tx(function_name, 'ERA', tx_hash, private_key)
            sleeping(SLEEP_APPROVE_MIN, SLEEP_APPROVE_MAX)
            if (result != 1 and retry > 0):
                retry = retry - 1
                result = approve_token(private_key, web3, address_contract, amount_wei, router_address, scan, SRC_CHAIN, retry)
            return result
    except Exception as error:
        cprint(f'>>> Exception {function_name} {amount_wei} {SRC_CHAIN}: {error}', 'red')
        with open(log_folder+f'/fail_{function_name}.txt', 'a') as f:
                f.write(f"{private_key} \n")
        sleeping(SLEEP_MIN, SLEEP_MAX)
        result = -1
        if (retry > 0):
            retry = retry - 1
            result = approve_token(private_key, web3, address_contract, amount_wei, router_address, scan, SRC_CHAIN, retry)
        return result


def check_status_tx(chain, tx_hash):
    counter = 0
    while True:
        try:
            data = check_rpc(chain)
            rpc_chain = data['rpc']
            web3        = Web3(Web3.HTTPProvider(rpc_chain))
            status_     = web3.eth.get_transaction_receipt(tx_hash)
            status      = status_["status"]
            if status in [0, 1]:
                return status
            time.sleep(1)
        except Exception as error:
            counter = counter +1 
            if (counter > TIME_OUT_LIMIT):
                logger.error(f'{chain} chain timeout. Skip this chain')
                return -1
            # logger.info(f'{counter} error, try again : {error}')
            time.sleep(1)
    
def  pritnt_status_tx(function_name, chain, tx_hash, key):
    status = check_status_tx(chain, tx_hash.hex())
    scan = check_rpc(chain)['scan']
    if status == 1:
        logger.success(f"{function_name} | {scan}/tx/{tx_hash.hex()}")
    else:
        logger.error(f"{function_name} | tx is failed | {scan}/tx/{tx_hash.hex()}")
        with open(log_folder+f'/fail_{function_name}.txt', 'a') as f:
            f.write(f"{key} \n")
    return status

def wait_normal_gas(normal_gas):
    gas_is_high = True
    while gas_is_high:
        eth_web3 = Web3(Web3.HTTPProvider(check_rpc('ETH')['rpc']))
        gas_price = eth_web3.eth.gas_price
        gas_price_gwei = round(eth_web3.from_wei(gas_price, 'gwei'))
        cprint(f'gas_price: {gas_price_gwei}. Normal price for script: {normal_gas}')
        if (gas_price_gwei <= normal_gas):
            gas_is_high = False
            continue
        time.sleep(30)