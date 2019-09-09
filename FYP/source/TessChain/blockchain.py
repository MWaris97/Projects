from functools import reduce
import json

from utility.hash_util import hash_block 
from utility.verificationHelper import VerficationHelper
from wallet import Wallet
from block import Block
from ballot import Ballot

import requests

# The reward we give to miners
PROVIDE_BALLOT = 1


class Blockchain:

    def __init__(self, node_key, node_id):
        #The starting block for the blockchain
        self.genesis_block = Block(0, '' , [], 100, 0)
        #Initializing our blockchain list
        self.chain = [self.genesis_block]
        #Unverified ballots
        self.__open_ballots = []
        # public key of the validator
        self.node_key = node_key
        #Id of the hosting node
        self.node_id = node_id
        self.__peer_nodes = set()
        # list of voters who have already cast vote
        self.__voter_list = []
        self.resolve_conflicts = False
        #Load data from the file
        self.load_data()


    @property
    def chain(self):
        return self.__chain[:]

    @chain.setter
    def chain(self, val):
        self.__chain = val

    def get_open_ballots(self):
        return self.__open_ballots[:]

    def load_data(self):
        """ Initialize blockchain and open ballot data from the file """
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='r') as f:
                file_content = f.readlines()
                blockchain = json.loads(file_content[0])
                updated_blockchain = []
                for block in blockchain:
                    converted_ballot = [Ballot(bt['voterId'], bt['voter_key'], bt['candidate'], bt['signature'], bt['vote']) for bt in block['ballot']]
                    updated_block = Block(block['index'], block['previous_hash'], converted_ballot, block['proof'], block['timestamp'])
                    updated_blockchain.append(updated_block)
                self.chain = updated_blockchain
                open_ballots = json.loads(file_content[1])
                updated_ballots = []
                # Converting open_ballots (list of dicts) to list of Ballot objects
                for bt in open_ballots:
                    updated_ballot = Ballot(bt['voterId'], bt['voter_key'], bt['candidate'], bt['signature'],bt['vote'])
                    updated_ballots.append(updated_ballot)  # make a lis of Ballot object
                self.__open_ballots = updated_ballots  #copy the converted list to open_ballots 
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
                voter_list = json.loads(file_content[3])
                self.__voter_list = voter_list
        except (IOError, IndexError):
            pass

    def save_data(self):
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='w') as f:
                # redundancy in code, convert to funtion
                saveable_chain = [block.__dict__ for block in [Block(block_el.index, block_el.previous_hash, [bt.__dict__ for bt in block_el.ballot], block_el.proof, block_el.timestamp) for block_el in self.__chain]]
                f.write(json.dumps(saveable_chain))
                saveable_ballot = [bt.__dict__ for bt in self.__open_ballots]
                f.write('\n' + json.dumps(saveable_ballot))
                f.write('\n' + json.dumps(list(self.__peer_nodes)))
                f.write('\n' + json.dumps(self.__voter_list))
        except IOError:
            print("A problem occured while saving the file!")

    def proof_of_work(self, last_hash):
        proof = 0
        
        while not VerficationHelper.valid_proof(self.__open_ballots,last_hash,proof):
            proof += 1
        return proof

    #This can be used for calculating the results

    def get_balance(self, voter_key):
        """ Calculate and return the balance for the node"""

        if voter_key == None:
                return None
        else:
            # to get the key of the sender, since it is no necessary that the
            # node that is verifying/adding the transaction has carried out 
            # the transaction itself
            participant = voter_key
        # Fetch a list of all sent coin amounts for the given person (Empty lists are returned if the person was NOT the sender)
        # This fetches sent amounts of transaction that were already included in the block
        voter_key = [[bt.vote for bt in block.ballot if bt.voter_key == participant] for block in self.__chain]
        # Fetch a list of all sent coin amounts for the given person (empty lists are returned if the person was NOT the sender)
        # This fetches sent amounts of open transactions (to avoid double spending)
        open_bt_sender = [bt.vote for bt in self.__open_ballots if bt.voter_key == participant]
        voter_key.append(open_bt_sender)
        # Calculates the total amount of coins sent
        amount_sent = reduce(lambda bt_sum, bt_amt: bt_sum + sum(bt_amt) if len(bt_amt) > 0 else bt_sum,voter_key, 0)
        # This fetches received coin amounts of transactions that were already included in the block
        # We ignore open transactions here because you shouldn't be able to spend coins before the transaction was confirmed
        candidate = [[bt.vote for bt in block.ballot if bt.candidate == participant] for block in self.__chain]
        # print(candidate)
        amount_recieved = reduce(lambda bt_sum, bt_amt: bt_sum + sum(bt_amt) if len(bt_amt) > 0 else bt_sum, candidate,0)
        # Return the total balance
        return amount_recieved - amount_sent

    def mine_block(self, voter_key, node_key):

        if self.node_key == None:
            return False

        last_block = self.__chain[-1]
        last_block_hash =  hash_block(last_block)

        proof = self.proof_of_work(last_block_hash)
        initial_ballot = Ballot(self.node_id, node_key, voter_key, '', PROVIDE_BALLOT)

        copied_ballots = self.__open_ballots[:] 

        #Verify signature before adding the transactions to the block
        for bt in copied_ballots:
            if not Wallet.verify_ballotSign(bt):
                return None
        
        copied_ballots.append(initial_ballot)
        block = Block(len(self.__chain), last_block_hash, copied_ballots, proof)

        self.__chain.append(block)
        self.__open_ballots = []
        self.save_data()

        for node in self.__peer_nodes:
                    url = 'http://{}/broadcast_block'.format(node)
                    converted_block = block.__dict__.copy()
                    converted_block['ballot'] = [bt.__dict__ for bt in converted_block['ballot']]
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
        ballots = [Ballot(bt['voterId'], bt['voter_key'], bt['candidate'], bt['signature'], bt['vote']) for bt in block['ballot']]
        proof_is_valid = VerficationHelper.valid_proof(ballots[:-1], block['previous_hash'], block['proof'])
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
        converted_block = Block(
            block['index'], block['previous_hash'], ballots, block['proof'], block['timestamp'])
        self.__chain.append(converted_block)
        # remove open ballots that has been added in the block
        stored_ballots = self.__open_ballots[:]
        for ibt in block['ballot']:
            for openbt in stored_ballots:
                if openbt.voterId == ibt['voterId'] and openbt.voter_key == ibt['voter_key'] and openbt.candidate == ibt['candidate'] and openbt.vote == ibt['vote'] and openbt.signature == ibt['signature']:
                    try:
                        self.__open_ballots.remove(openbt)
                    except ValueError:
                        print('Item was already removed') 
        self.save_data()
        return True


    def add_ballot(self, candidate, voterId, voter_key, signature, vote, voter_list, is_recieving = False):
        """ Adds a transaction value in the blockchain concatenated with previous transaction
        Arguments:
            :voterId: The ID of the voter
            :voter_key: The voter_key of the the voter
            :candidate: The candidate that the voter will choose
            :vote: default = 1
        """

        if self.node_key == None:
            return False

        temp_ballot = Ballot(voterId, voter_key, candidate, signature, vote)

        #Verify transaction before adding to open ballots        
        if VerficationHelper.verify_ballot(temp_ballot, self.get_balance):
            self.__open_ballots.append(temp_ballot)
            self.save_data()
            if not is_recieving:
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast_ballot'.format(node)
                    try:
                        response = requests.post(url, json = {
                            'voterId': voterId,
                            'voter_key': voter_key,
                            'candidate': candidate,
                            'vote': vote,
                            'signature': signature,
                            'voter_list': voter_list})
                        if response.status_code == 400 or response.status_code == 500:
                            print('Ballot declined, need resolving!')
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
                [Ballot(bt['voterId'], bt['voter_key'], bt['candidate'], bt['signature'], 
                bt['vote']) for bt in block['ballot']], 
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
            self.__open_ballots = []

        self.save_data()
        return replaced


    def count_votes(self, candidate):
        candidates = [[bt.vote for bt in block.ballot if bt.candidate == candidate] for block in self.__chain]
        if candidates == []:
            return False
        # print(candidate)
        total_votes = reduce(lambda bt_sum, bt_amt: bt_sum + sum(bt_amt) if len(bt_amt) > 0 else bt_sum, candidates,0)
        # Return the total balance
        return total_votes


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

    
    def addto_voter_list(self, voterId):
        """ Adds the voterId to the voter list after the voter cast his/her vote.

        Arguments:
            :voterId: ID of the voter e.g. 16CSXX
        """
        self.__voter_list.append(voterId)
        self.save_data()

    
    def get_voter_list(self):
        """ Return list of voters who have already cast vote"""
        return self.__voter_list