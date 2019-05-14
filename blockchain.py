#!/usr/bin/env python3.5

import base64
import itertools
import json
from hashlib import sha256
from math import floor
from time import time
from typing import List

from fastecdsa import curve, ecdsa, keys

from console_logging.console import Console
# A cool terminal output logger
# initialized
console = Console()

# A helper class for the little hack i did with the ecdsa public keys
# This converts it hex back to points in a the curve secp256k1
class CurvePoint:
    """
    Returns points from the signature for verifcation
    """
    # First get the x, y like the original public keys
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    # Then create a nice output like the default one from the key
    # you can pass a different curve if used different, but i doubt it
    # would look the same
    def __str__(self) -> str:
        return 'X: {}\nY: {}\n(On curve <{}>)'.format(hex(self.x), hex(self.y), 'secp256k1')


# Our block class
class Block:
    """
    timestamp{number}
    transactions{Transaction[]}
    previousHash{string}
    """
    # Creates an instance of an iterable for the class ids
    block_id = itertools.count()
    # Initialize a class with all the required values
    def __init__(self, timestamp: int, transactions: List[object], previousHash='') -> None:
        self.id = next(self.block_id)
        self.previousHash = previousHash
        self.timestamp = timestamp
        self.transactions = transactions
        self.nonce = 0
        self.hash = self.calculateHash()

    # This method calculates the hash this block will store as/for reference of
    # the previous hash, transactions, timestamp and nonce
    def calculateHash(self) -> str:
        """
        Returns the SHA256 of this block(by processing all the data stored
        inside this block)
        """
        # The try/except code block is for the times when the transactions are empty
        # and the json.dumps method returns a type error, hence, string it!!
        try:
            temp = str(self.previousHash) + str(self.timestamp) + json.dumps(self.transactions) + str(self.nonce)
        except TypeError:
            temp = str(self.previousHash) + str(self.timestamp) + str(self.transactions) + str(self.nonce)
        
        return sha256(temp.encode('utf-8')).hexdigest()

    # Method to mine our *pending transactions in blocks after signing
    def mineBlock(self, difficulty: int) -> None:
        """
        Starts the mining process on the block. It changes the 'nonce' until the hash
        of the block starts with enough zeros(=difficulty)
        """
        # Here the logic(Proof Of Work/PoW) is that the method has to
        # find the hash that has the exact amout of zeros in the beginning
        # as to the difficulty amount
        # the higher the difficulty, the longer the time taken
        ## TODO - Try using lru_cache function to speed up process(But why!)
        while self.hash[0:difficulty] != str('0' * difficulty):
            # Increment the nonce by 1 each time to see the loop count
            self.nonce += 1
            self.hash = self.calculateHash()

        console.info('Block mined: {}'.format(self.hash))

    # Method that checks ifthe transactions in the block are all valid(Incuding Reward)
    def hasValidTransactions(self) -> bool:
        """
        Validates all the transactions inside this block(signature + hash) and
        returns true if everything checks out. False if the block is invalid.
        """
        # Loop through all availvable transactions
        for tx in self.transactions:
            if not tx.isValid():
                return False

        return True


# THe transactions in our blocks
class Transaction:
    """
    fromAddress{string}
    toAddress{string}
    amount{number}
   """
    # Creates an instance of an iterable for the class ids
    trans_id = itertools.count()
    # Initialize a class with all the required values
    def __init__(self, fromAddress: str, toAddress: str, amount: int) -> None:
        self.id = next(self.trans_id)
        self.fromAddress = fromAddress
        self.toAddress = toAddress
        self.amount = amount
        self.timestamp = floor(time())

    # Calculate the hash for our Transaction returning a hex string
    def calculateHash(self) -> str:
        temp = str(self.fromAddress) + str(self.toAddress) + str(self.amount) + str(self.timestamp)
        return sha256(temp.encode('utf-8')).hexdigest()

    # Signs our Transaction with our signing key/private keyy(generated)
    def signTransaction(self, signingKey: int) -> None:
        """
        You can only send a transaction from the wallet that is linked to your
        key. So here we check if the fromAddress matches your publicKey
        """
        # Get our public key from the private/signing key
        pub_key = keys.get_public_key(signingKey, curve.secp256k1)
        # Turn it to a hex key for easy handling
        pub_key_hex = hex(int(str(pub_key.x)+str(pub_key.y)))
        # Ensure the public hex and the sender adddress are the same
        # security check, else raise exception
        if pub_key_hex != self.fromAddress:
            raise Exception('You cannot sign transactions for other wallets!')

        # Calculate the hash of this transaction, sign it with the key
        # and store it inside the transaction object
        hashTx = self.calculateHash()
        r, s = ecdsa.sign(hashTx, signingKey, curve=curve.secp256k1)
        # Did alittle hacking to get the signature into on variable and
        # hex it for easier handling
        sig = int(str(r)+str(s))

        self.signature = hex(sig)

    # Method to check if the transaction is valid
    def isValid(self) -> bool:
        """
        If the transaction doesn't have a from address we assume it's a
        mining reward and that it's valid. You could verify this in a
        different way(special field for instance)
        """
        # if the sender address is None or empty, it means
        # this is a reward transaction
        if self.fromAddress == None:
            return True

        if not self.signature or len(self.signature) == 0:
            raise Exception('No signature in this transaction')

        r, s = int(str(int(self.signature, 0))[:77]), int(str(int(self.signature, 0))[77:])
        pub_key = CurvePoint(int(str(int(self.fromAddress, 0))[:77]), int(str(int(self.fromAddress, 0))[77:]))
        return ecdsa.verify((r, s), self.calculateHash(), pub_key, curve=curve.secp256k1)


# Our actual chain of blocks :)
class Blockchain:
    """
    The chain of all the blocks
    """
    # Creates an instance of an iterable for the class ids
    blockchain_id = itertools.count()
    # Initialize a class with all the required values
    def __init__(self) -> None:
        self.id = next(self.blockchain_id)
        self.chain = [self.createGenesisBlock()]
        self.difficulty = 2
        self.pendingTransactions = []
        self.miningReward = 100

    # Creates a genesis block, which is the 1st block in our chain
    def createGenesisBlock(self) -> Block:
        return Block(floor(time()), [], '0')

    # This methods return the latest block in the chain
    def getLatestBlock(self) -> Block:
        """
        Returns the latest block on our chain. Useful when you want to create a
        new Block and you need the hash of the previous Block.
        """
        return self.chain[len(self.chain) - 1]

    # This methods mines all the pending transactions in the block
    def minePendingTransactions(self, miningRewardAddress: str) -> None:
        """
        Takes all the pending transactions, puts them in a Block and starts the
        mining process. It also adds a transaction to send the mining reward to
        the given address.
        """
        # Create a reward transaction to your address from system for every mined block
        rewardTx = Transaction(None, miningRewardAddress, self.miningReward)
        self.pendingTransactions.append(rewardTx)

        block = Block(floor(time()), self.pendingTransactions, self.getLatestBlock().hash)
        block.mineBlock(self.difficulty)

        console.success('Block successfully mined!')
        self.chain.append(block)

        self.pendingTransactions = []

    # This method addds created transactions to the pending list
    def addTransaction(self, transaction: Transaction) -> None:
        """
        Add a new transaction to the list of pending transactions(to be added
        next time the mining process starts). This verifies that the given
        transaction is properly signed.
        """
        # Check if both address are provided
        if not transaction.fromAddress or not transaction.toAddress:
            raise Exception('Transaction must include from and to address')

        # Verify the transactiion
        if not transaction.isValid():
            raise Exception('Cannot add invalid transaction to chain')

        # Verify transaction amount isnt empty
        if transaction.amount <= 0:
            raise Exception('Transaction amount should be higher than 0')

        self.pendingTransactions.append(transaction)

    # Returns the account balance of a given address
    def getBalanceOfAddress(self, address: str) -> int:
        """
        Returns the balance of a given wallet address.
        """
        # balance always starts at zero
        balance = 0

        # Loop through the chain for blocks then
        for block in self.chain:
            # loop through blocks for transactions then
            for trans in block.transactions:
                # check if the address is yours
                if trans.fromAddress == address:
                    # deduce the amount for each transaction made
                    balance -= trans.amount

                # if its not then
                if trans.toAddress == address:
                    # add to your balance for mining rewards
                    balance += trans.amount

        return balance

    # This method returns all the transactions from the given wallet address
    def getAllTransactionsForWallet(self, address: str) -> List[Transaction]:
        """
        Returns a list of all transactions that happened
        to and from the given wallet address.
        """
        txs = []

        # Loop through the chain then
        for block in self.chain:
            # loop through the transactions then
            for tx in block.transactions:
                # check where the address is from
                if (tx.fromAddress == address or tx.toAddress == address):
                    txs.append(tx)

        return txs

    # This method checks if the chain has been tapered with
    def isChainValid(self) -> bool:
        """
        Loops over all the blocks in the chain and verify if they are properly
        linked together and nobody has tampered with the hashes. By checking
        the blocks it also verifies the(signed) transactions inside of them.
        """
        # Check if the Genesis block hasn't been tampered with by comparing
        # the output of createGenesisBlock with the first block on our chain
        realGenesis = self.createGenesisBlock().hash

        chainValue = self.chain[0].hash

        if realGenesis != chainValue:
            return False

        # Check the remaining blocks on the chain to see if there hashes and
        # signatures are correct
        for i in range(1, len(self.chain)):
            currentBlock = self.chain[i]
            previousBlock = self.chain[i - 1]

            if not currentBlock.hasValidTransactions():
                return False

            if currentBlock.hash != currentBlock.calculateHash():
                return False

            if currentBlock.previousHash != previousBlock.calculateHash():
                return False

        return True
