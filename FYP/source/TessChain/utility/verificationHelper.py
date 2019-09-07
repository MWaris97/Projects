"""Provides verification helper methods"""

from utility.hash_util import hash_block, hash_string_256
from wallet import Wallet


class VerficationHelper:
   
    @staticmethod
    def valid_proof(ballots, last_hash, proof):
        guess = (str([bt.to_ordered_dict() for bt in ballots]) + str(last_hash) + str(proof)).encode() 
        guess_hash = hash_string_256(guess)
        # print(guess_hash)
        return guess_hash[0:4] == '0000'

    @classmethod
    def verify_chain(cls, blockchain):
        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index-1]):
                return False

            if not cls.valid_proof(block.ballot[:-1], block.previous_hash, block.proof):
                print('Proof of work is invalid')
                return False
        return True

    @staticmethod
    def verify_ballot(ballot, get_balance, check_funds=True):
        if check_funds == True:
            voter_balance = get_balance(ballot.voter_key)
            return voter_balance >= ballot.vote and Wallet.verify_ballotSign(ballot)
        else:
            return Wallet.verify_ballotSign(ballot)

    @classmethod
    def verify_allTrax(cls, open_ballot, get_balance):
        return all([cls.verify_ballot(el,get_balance, False) for el in open_ballot])