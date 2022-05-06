#!/usr/bin/env python3

# APTOS faucet and balance code example

# Copyright (c) idonotknowwhatimdoing 
# Contact https://t.me/WhiteCacao

from ctypes import addressof
import requests
import argparse
import time
from typing import Any, Dict, Optional

TESTNET_URL = "https://fullnode.devnet.aptoslabs.com"
FAUCET_URL = "https://faucet.devnet.aptoslabs.com"

aparser = argparse.ArgumentParser(description='APTOS faucet and balance code example')
aparser.add_argument("--f", default="NONE", help="Add coins to address")
aparser.add_argument("--b", default="NONE", help="View the address balance")
args = aparser.parse_args()
f = args.f
b = args.b

class RestClient: 
    def __init__(self, url: str) -> None:
        self.url = url

    def account_resource(self, account_address: str, resource_type: str) -> Optional[Dict[str, Any]]:
        response = requests.get(f"{self.url}/accounts/{account_address}/resource/{resource_type}")
        if response.status_code == 404:
            return None
        assert response.status_code == 200, response.text
        return response.json()

    def transaction_pending(self, txn_hash: str) -> bool:
        response = requests.get(f"{self.url}/transactions/{txn_hash}")
        if response.status_code == 404:
            return True
        assert response.status_code == 200, f"{response.text} - {txn_hash}"
        return response.json()["type"] == "pending_transaction"

    def wait_for_transaction(self, txn_hash: str) -> None:
        count = 0
        while self.transaction_pending(txn_hash):
            assert count < 10, f"transaction {txn_hash} timed out"
            time.sleep(1)
            count += 1
        response = requests.get(f"{self.url}/transactions/{txn_hash}")
        assert "success" in response.json(), f"{response.text} - {txn_hash}"

    def account_balance(self, account_address: str) -> Optional[int]:
        return self.account_resource(account_address, "0x1::TestCoin::Balance")

class FaucetClient:
    def __init__(self, url: str, rest_client: RestClient) -> None:
        self.url = url
        self.rest_client = rest_client

    def fund_account(self, address: str, amount: int) -> None:
        txns = requests.post(f"{self.url}/mint?amount={amount}&address={address}")
        assert txns.status_code == 200, txns.text
        for txn_hash in txns.json():
            self.rest_client.wait_for_transaction(txn_hash)

if __name__ == "__main__":
    rest_client = RestClient(TESTNET_URL)
    faucet_client = FaucetClient(FAUCET_URL, rest_client)

    if f != "NONE": 
        print(f"Current address balance: {rest_client.account_balance(f)}")
        faucet_client.fund_account(f, 1_000_000)
        print(f"Updated address balance: {rest_client.account_balance(f)}")

    if b != "NONE": print(f"Current address balance: {rest_client.account_balance(b)}")
