from functools import reduce
import json

from utility.hash_util import hash_block 
from utility.verificationHelper import VerficationHelper
from wallet import Wallet
from block import Block
from trax import Trax

import requests

# The reward we give to miners
MINING_REWARD = 10


class Blockchain:

    def __init__(self, public_key, node_id):
        #The starting block for the blockchain
        self.genesis_block = Block(0, '' , [], 100, 0)
        #Initializing our blockchain list
        self.chain = [self.genesis_block]
        #Unhandeled transactions
        self.__open_trax = []
        #Id of the hosting node
        self.public_key = public_key
        self.node_id = node_id
        self.__peer_nodes = set()
        self.resolve_conflicts = False
        #Load data from the file
        self.load_data()


    @property
    def chain(self):
        return self.__chain[:]

    @chain.setter
    def chain(self, val):
        self.__chain = val

    def get_open_trax(self):
        return self.__open_trax[:]

    def load_data(self):
        """ Initialize blockchain and open trax data from the file """
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='r') as f:
                file_content = f.readlines()
                blockchain = json.loads(file_content[0])
                updated_blockchain = []
                for block in blockchain:
                    converted_trax = [Trax(tx['tx_sender'], tx['tx_recipient'], tx['signature'], tx['tx_amount']) for tx in block['trax']]
                    updated_block = Block(block['index'], block['previous_hash'], converted_trax, block['proof'], block['timestamp'])
                    updated_blockchain.append(updated_block)
                self.chain = updated_blockchain
                open_trax = json.loads(file_content[1])
                updated_traxs = []
                # Converting open_trax (list of dicts) to list of Trax objects
                for tx in open_trax:
                    updated_trax = Trax(tx['tx_sender'], tx['tx_recipient'], tx['signature'],tx['tx_amount'])
                    updated_traxs.append(updated_trax)  # make a lis of Trax object
                self.__open_trax = updated_traxs  #copy the converted list to open_trax 
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError):
            pass

    def save_data(self):
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='w') as f:
                # redundancy in code, convert to funtion
                saveable_chain = [block.__dict__ for block in [Block(block_el.index, block_el.previous_hash, [tx.__dict__ for tx in block_el.trax], block_el.proof, block_el.timestamp) for block_el in self.__chain]]
                f.write(json.dumps(saveable_chain))
                saveable_trax = [tx.__dict__ for tx in self.__open_trax]
                f.write('\n' + json.dumps(saveable_trax))
                f.write('\n' + json.dumps(list(self.__peer_nodes)))
        except IOError:
            print("A problem occured while saving the file!")

    def proof_of_work(self, last_hash):
        proof = 0
        
        while not VerficationHelper.valid_proof(self.__open_trax,last_hash,proof):
            proof += 1
        return proof

    def get_balance(self, tx_sender=None):
        """ Calculate and return the balance for the node"""

        if tx_sender == None:
            if self.public_key == None:
                return None
            participant = self.public_key
        else:
            # to get the key of the sender, since it is no necessary that the
            # node that is verifying/adding the transaction has carried out 
            # the transaction itself
            participant = tx_sender
        # Fetch a list of all sent coin amounts for the given person (Empty lists are returned if the person was NOT the sender)
        # This fetches sent amounts of transaction that were already included in the block
        tx_sender = [[tx.tx_amount for tx in block.trax if tx.tx_sender == participant] for block in self.__chain]
        # Fetch a list of all sent coin amounts for the given person (empty lists are returned if the person was NOT the sender)
        # This fetches sent amounts of open transactions (to avoid double spending)
        open_tx_sender = [tx.tx_amount for tx in self.__open_trax if tx.tx_sender == participant]
        tx_sender.append(open_tx_sender)
        print(tx_sender)
        # print(tx_sender)
        # Calculates the total amount of coins sent
        amount_sent = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum,tx_sender, 0)
        # This fetches received coin amounts of transactions that were already included in the block
        # We ignore open transactions here because you shouldn't be able to spend coins before the transaction was confirmed
        tx_recipient = [[tx.tx_amount for tx in block.trax if tx.tx_recipient == participant] for block in self.__chain]
        # print(tx_recipient)
        amount_recieved = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum, tx_recipient,0)
        # Return the total balance
        return amount_recieved - amount_sent

    def mine_block(self):

        if self.public_key == None:
            return False

        last_block = self.__chain[-1]
        last_block_hash =  hash_block(last_block)

        proof = self.proof_of_work(last_block_hash)
        reward_transaction = Trax('MINING', self.public_key, '', MINING_REWARD)
        # reward_transaction = OrderedDict(
        #     [('sender', 'MINING'),('recipient', owner), ('amount', MINING_REWARD)])

        copied_trax = self.__open_trax[:] 

        #Verify signature before adding the transactions to the block
        for tx in copied_trax:
            if not Wallet.verify_traxSign(tx):
                return None
        
        copied_trax.append(reward_transaction)
        block = Block(len(self.__chain), last_block_hash, copied_trax, proof)

        self.__chain.append(block)
        self.__open_trax = []
        self.save_data()

        for node in self.__peer_nodes:
                    url = 'http://{}/broadcast_block'.format(node)
                    converted_block = block.__dict__.copy()
                    converted_block['trax'] = [tx.__dict__ for tx in converted_block['trax']]
                    try:
                        response = requests.post(url, json = {
                            'block': converted_block
                        })
                        if response.status_code == 400 or response.status_code == 500:
                            print('Block declined, need resolving!')
                        if response.status_code == 409:
                            self.resolve_conflicts = True
                    except requests.exceptions.ConnectionError:
                        continue
        return block

        
    def add_block(self, block):
        transactions = [Trax(tx['tx_sender'], tx['tx_recipient'], tx['signature'], tx['tx_amount']) for tx in block['trax']]
        proof_is_valid = VerficationHelper.valid_proof(transactions[:-1], block['previous_hash'], block['proof'])
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
        converted_block = Block(
            block['index'], block['previous_hash'], transactions, block['proof'], block['timestamp'])
        self.__chain.append(converted_block)
        # remove open transactions that has been added in the block
        stored_transactions = self.__open_trax[:]
        for itx in block['trax']:
            for opentx in stored_transactions:
                if opentx.tx_sender == itx['tx_sender'] and opentx.tx_recipient == itx['tx_recipient'] and opentx.tx_amount == itx['tx_amount'] and opentx.signature == itx['signature']:
                    try:
                        self.__open_trax.remove(opentx)
                    except ValueError:
                        print('Item was already removed') 
        self.save_data()
        return True


    def add_trax(self, recipient, sender,signature, amount = 1.0, is_recieving = False):
        """ Adds a transaction value in the blockchain concatenated with previous transaction
        Arguments:
            :sender: The sender of the coins
            :recipient: The recipient of the coins.
            :amount: The amount of coins sent with the transaction (default = 1.0)
        """
        # temp_trax = {
        #     'sender': sender, 
        #     'recipient': recipient, 
        #     'amount': amount
        # }
        if self.public_key == None:
            return False

        temp_trax = Trax(sender, recipient, signature, amount)

        #Verify transaction before adding to open transactions        
        if VerficationHelper.verify_trax(temp_trax, self.get_balance):
            self.__open_trax.append(temp_trax)
            self.save_data()
            if not is_recieving:
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast_trax'.format(node)
                    try:
                        response = requests.post(url, json = {
                            'tx_sender': sender,
                            'tx_recipient': recipient,
                            'tx_amount': amount,
                            'signature': signature})
                        if response.status_code == 400 or response.status_code == 500:
                            print('Transaction declined, need resolving!')
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
            return True
        return False


    def resolve(self):
        winner_chain = self.chain
        replaced = False
        for node in self.__peer_nodes:
            url = 'http://{}/chain'.format(node) 
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [Block(block['index'], block['previous_hash'], 
                [Trax(tx['tx_sender'], tx['tx_recipient'], tx['signature'], 
                tx['tx_amount']) for tx in block['trax']], 
                block['proof'], block['timestamp']) for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(winner_chain)

                if node_chain_length > local_chain_length and VerficationHelper.verify_chain(node_chain):
                    winner_chain = node_chain
                    replaced = True

            except requests.exceptions.ConnectionError:
                continue

        self.resolve_conflicts = False
        self.chain = winner_chain

        if replaced:
            self.__open_trax = []

        self.save_data()
        return replaced


    def add_peer_node(self, node):
        """ Adds a new node to the peer node set.

        Arguments:
            :node: The node URL which should be added, 
        """
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        """ Removes a node from the peer node set.

        Arguments:
            :node: The node URL which should be removed, 
        """
        self.__peer_nodes.discard(node)
        self.save_data

    def get_peer_nodes(self):
        """ Return a list of all connected peer nodes."""
        return list(self.__peer_nodes)