from solcx import compile_standard, install_solc
import json
from web3 import Web3
from dotenv import load_dotenv
from os import getenv

load_dotenv()

# * Install solc compiler if not installed (i think)
print("Installing...")
install_solc("0.8.8")
print("Installed!")

with open("./SimpleStorage.sol", "r") as file:
    simple_storage_file = file.read()

# * get the solidity source code and compile
compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"SimpleStorage.sol": {"content": simple_storage_file}},
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode", "evm.bytecode.sourceMap"]
                }
            }
        },
    },
    solc_version="0.8.8",
)

with open("compiled_code.json", "w") as file:
    json.dump(compiled_sol, file)

# * get bytecode
bytecode = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["evm"][
    "bytecode"
]["object"]

# * get abi
abi = json.loads(
    compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]["metadata"]
)["output"]["abi"]

# * Connecting to Ganache
w3 = Web3(Web3.HTTPProvider(getenv("RPC_URL")))
network_id = 5777 # Seems like this is not actually needed.
my_address = getenv("PUBLIC_KEY")
private_key = getenv("PRIVATE_KEY")
# print(Web3.toChecksumAddress("A1c6bA7bCDFC20C2B09B8F09263bE19F0179044c"))

# * Creating the contract in python
SimpleStorage = w3.eth.contract(abi=abi, bytecode=bytecode)

# * Get the latest transaction count
nonce = w3.eth.getTransactionCount(my_address)
# print(nonce)  # nonce is the transaction count in this case.
# print(dir(w3))

# notes: 3 steps of doing a transaction ( performing a state change in blockchain )
# * 1.Build the transaction
# * 2.Sign the transaction
# * 3.Send the transaction

# * 1.
txn = SimpleStorage.constructor().buildTransaction(
    # print(w3.eth.gas_price)
    # print(w3.eth.chain_id)
    {
        "chainId": w3.eth.chain_id,
        "from": my_address,
        "nonce": nonce,
        "gasPrice": w3.eth.gas_price,
    }
)
# print(txn)

# * 2.
signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
# print(signed_txn)

# * 3.
txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
# print("txn_hash :", txn_hash)
txn_reciept = w3.eth.wait_for_transaction_receipt(
    txn_hash
)  # This waits until the transaction finishes.
# print("txn_reciept :", txn_reciept)


# notes: 2 things that are needed to interact with any contract is contract addr. & abi
# * Interacting with the contract using abi and address
simple_storage_instance = w3.eth.contract(address=txn_reciept.contractAddress, abi=abi)
# print(
#     simple_storage_instance,
#     "\nADDRESS :",
#     simple_storage_instance.address,
#     f"\n\n{dir(simple_storage_instance)}",
# )

# notes: Call vs Transact
# Call => Simulates the transaction and return value. Not recognized as a contract interaction in Ganache.
# Transact => Make a actual state change

print(simple_storage_instance.functions.retrieve()) # <Function retrieve() bound to ()>
print(f"Initial Stored Value : {simple_storage_instance.functions.retrieve().call()}") # returns 0. seems like uint256 initialized with zero by default.
print(simple_storage_instance.functions.store(3)) # <Function store(uint256) bound to (3,)>
print(simple_storage_instance.functions.store(3).call()) # returns empty array b'cos store function does not return anything.

# * Transaction Store using same 3 steps
store_txn = simple_storage_instance.functions.store(15).buildTransaction(
    {
        "chainId": w3.eth.chain_id,
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce + 1,
    }
)
signed_store_txn = w3.eth.account.sign_transaction(
    store_txn, private_key=private_key
)
tx_store_hash = w3.eth.send_raw_transaction(signed_store_txn.rawTransaction)
print("\nUpdating stored Value...")
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_store_hash)

print(f"Updated Value : {simple_storage_instance.functions.retrieve().call()}")