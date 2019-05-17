#!/usr/bin/env python3.5
import json
# import logging
import os
import time
from typing import List
from datetime import datetime

# import werkzeug.serving
from fastecdsa import curve, ecdsa, keys
from flask import Flask, jsonify, redirect, render_template, request, url_for
# from gevent import pywsgi

from blockchain import Blockchain, Transaction
# from console_log import ConsoleLog
from flask_cors import *
# from geventwebsocket.handler import WebSocketHandler

# Initailizing the Flask app
APP = Flask(__name__)
# Configuring a secret key
APP.config['SECRET_KEY'] = os.urandom(64)
# Setting up CORS for AJAX calls
cors = CORS(APP)

# Initializing and configuring the logger
# for both Python and Web Console
# logger = logging.getLogger('console')
# logger.setLevel(logging.DEBUG)

# Your private key goes here
PRIVATE_KEY = keys.gen_private_key(curve.secp256k1)

# From that we can calculate your public key(which doubles as your wallet address)
PUBLIC_KEY = keys.get_public_key(PRIVATE_KEY, curve.secp256k1)
myWalletAddress = hex(int(str(PUBLIC_KEY.x)+str(PUBLIC_KEY.y)))

# Create new instance of Blockchain class
blockchain = Blockchain()

### Demo Transactions
# This Block creates the sample block in the Demo
TX1 = Transaction(myWalletAddress, '123456789', 100)
TX1.signTransaction(PRIVATE_KEY)
try:
    try:
        blockchain.addTransaction(TX1)
    except ecdsa.EcdsaError:
        redirect('/', code=500)
except:
    redirect('/', code=500)


TX2 = Transaction(myWalletAddress, '987654321', 50)
TX2.signTransaction(PRIVATE_KEY)
try:
    try:
        blockchain.addTransaction(TX2)
    except ecdsa.EcdsaError:
        redirect('/', code=500)
except:
    redirect('/', code=500)

# Mine block
blockchain.minePendingTransactions(myWalletAddress)
### End Demo Transactions

# Store all wallet keys(incase you use more than one)
walletKeys = []
walletKeys.append({\
    'name': 'Me',\
    'PrivateKey': hex(PRIVATE_KEY),\
    'PublicKey': hex(int(str(PUBLIC_KEY.x)+str(PUBLIC_KEY.y)))\
    })
BLOCKS = blockchain.chain
SELECTEDBLOCK = 0
SHOWINFOMESSAGE = True
TRANSACTIONS = []
# DIFFICULTY = blockchain.difficulty
# REWARD = blockchain.miningReward
JUSTADDEDTX = False
NEWTX = None

# This helper method returns all transactions, if any, from the block passed
def transacts(selectedBlock: int) -> List[Transaction]:
    """
    Returns all the transactions, if any, from the passed block
    """
    trans = [block for block in BLOCKS if str(block.id) == str(selectedBlock)]
    return trans[0].transactions

# Just a variable to pass the server year to all the templates footer
YEAR = '{0:%Y}'.format(datetime.now())

## Routing begins here, organisation is abit different than normal
## AJAX ROUTES
# Route to select a block to see its transactions
@APP.route('/_select_block', methods=['GET'])
# @cross_origin(headers=['Content-Type'])
def select_block():
    """
    Sets the selected block and displays it transactions
    """
    global SELECTEDBLOCK, TRANSACTIONS
    SELECTEDBLOCK = request.args.get('block_id', 0, type=int)
    TRANSACTIONS = transacts(SELECTEDBLOCK)
    return jsonify(result=SELECTEDBLOCK)

# Route to dismiss the alert intro message
@APP.route('/_dismissInfo', methods=["GET"])
def dismissInfo():
    """
    Sets showInfoMessage to false so that the message is not displayed
    in every page you visit
    """
    global SHOWINFOMESSAGE
    SHOWINFOMESSAGE = request.args.get('value')
    # logger.info({'status': 200, 'message': 'Dissmised'})
    return jsonify({'status': 200, 'message': 'Dissmised'})

# Route to set the settings value
## TODO needs some more work
@APP.route('/_set_settings', methods=['GET'])
def set_settings():
    """
    Sets the difficulty and reward values for mining from the page to the code
    """
    # global DIFFICULTY, REWARD
    blockchain.difficulty = request.args.get('difficulty', blockchain.difficulty, type=int)
    blockchain.miningReward = request.args.get('reward', blockchain.miningReward, type=int)
    # print(DIFFICULTY)
    # print(REWARD)
    # logger.debug(DIFFICULTY)
    # logger.debug(REWARD)
    return jsonify(difficulty=blockchain.difficulty, reward=blockchain.miningReward)

# Route to create, sign and add Transactions to mining queue
@APP.route('/_create_transaction', methods=['POST'])
def create_transaction():
    """
    Creates, signs and add transaction to pending queue waiting for mining
    """
    global JUSTADDEDTX, NEWTX
    JUSTADDEDTX = True
    NEWTX = Transaction(myWalletAddress, request.form.get('toAddress'), int(request.form.get('amount')))
    NEWTX.signTransaction(PRIVATE_KEY)
    # This extra try/except is neccessary for the bug i havent been able to fix yet
    try:
        try:
            blockchain.addTransaction(NEWTX)
        except ecdsa.EcdsaError:
            blockchain.addTransaction(NEWTX)
    except:
        try:
            blockchain.addTransaction(NEWTX)
        except ecdsa.EcdsaError:
            blockchain.addTransaction(NEWTX)
    return redirect(url_for('pending'))

# Route to mine the queued transactions(pending transactions)
@APP.route('/_mine_transactions', methods=['POST'])
def mine_transactions():
    """
    Mines all the transactions in the queue(pending transactions)
    """
    global JUSTADDEDTX
    JUSTADDEDTX = False
    blockchain.minePendingTransactions(myWalletAddress)
    # logger.info({'status': 200, 'message': 'Mined'})
    return jsonify({'status': 200, 'message': 'Mined'})
## END AJAX ROUTES

## Here begins the main routes for the templates
## MAIN ROUTES
# Route to the index/main/front page of our app
@APP.route("/")
def index():
    """
    Displays the index/main/front page for our app
    including our blockchains blocks
    """
    # logger.error('Error logged from Python')
    # logger.warning('Warning logged from Python')
    # logger.info('Info logged from Python')
    # logger.debug({'foo': ['bar', 'baz']})
    return render_template('index.html', blocks=BLOCKS)

# Route to the settings page
@APP.route('/settings')
def settings():
    """
    Displays the template to set the difficulty and reward values
    """
    return render_template('settings.html', difficulty=blockchain.difficulty, reward=blockchain.miningReward)

# Route to the transaction creation form
@APP.route('/new/transaction')
def new_transaction():
    """
    Displays the template with the form to create transactions
    """
    return render_template('create-transaction.html', ownAddress=myWalletAddress)

# Route to transaction queue/pending transactions template
@APP.route('/transactions/pending')
def pending():
    """
    Displays the template with all the transacions added to the queue
    or pending transactions
    """
    return render_template('pending.html', pendingTransactions=blockchain.pendingTransactions, justAddedTx=JUSTADDEDTX)

# Route to wallet profile
@APP.route("/wallet/<string:address>")
def wallet(address):
    """
    Displays the template with details about the given address
    incuding balance, transactions done
    """
    balance = blockchain.getBalanceOfAddress(address)
    transactions = blockchain.getAllTransactionsForWallet(address)
    return render_template('wallet.html', walletAddress=address, myWalletAddress=myWalletAddress, balance=balance, transactions=transactions)
## END MAIN ROUTES


# Contains all the context need in the overall app, not specific to route
@APP.context_processor
def context_processor():
    def convert(timestamp: int) -> time:
        """
        Converts the time value(either int or str) into human readable
        time and date
        """
        value = time.ctime(int(timestamp))
        return value

    def addressIsFromCurrentUser(address: str) -> bool:
        if address == myWalletAddress:
            return True
        return False
    return dict(blockchain=blockchain, showInfoMessage=SHOWINFOMESSAGE, convert=convert, year=YEAR, selectedBlock=SELECTEDBLOCK, transactions=TRANSACTIONS, addressIsFromCurrentUser=addressIsFromCurrentUser, enumerate=enumerate, str=str, type=type, json=json, len=len)

## Custom error handling pages, just for fun
# 404 error handling template
@APP.errorhandler(404)
def not_found_error(error):
    """
    Render a custom 404 page that looks better than the original
    """
    # logger.error('Sorry, page not found..!')
    return render_template('404.html'), 404

# 500 error handling template
@APP.errorhandler(500)
def internal_server_error(error):
    """
    Render a custom 500 page that looks better than the original
    """
    # logger.error('Server error, sorry, try reloading..!')
    return render_template('500.html'), 500

# Create a console logging app by passing the app and
# the logger object to the ConsoleLog class
# APP = ConsoleLog(APP, logger)

# Custom main for the Web console logging to work
# it intercepts the logger and uses a web socket to
# padd the data to the console log of the browser(Something like that)
# @werkzeug.serving.run_with_reloader
# def main():
#     """
#     Creates a wsgi server for our app with a handler web socket for the logger
#     """
#     server = pywsgi.WSGIServer(("", 5000), APP, handler_class=WebSocketHandler)
#     server.serve_forever()


# The main runnable function, calls the main function
if __name__ == '__main__':
    # main()
    APP.run()
