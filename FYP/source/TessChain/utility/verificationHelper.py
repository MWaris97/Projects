"""Provides verification helper methods"""

from utility.hash_util import hash_block, hash_string_256
from wallet import Wallet


class VerficationHelper:
   
    @staticmethod
    def valid_proof(transactions, last_hash, proof):
        guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof)).encode() 
        guess_hash = hash_string_256(guess)
        # print(guess_hash)
        return guess_hash[0:3] == '000'

    @classmethod
    def verify_chain(cls, blockchain):
        for (index, block) in enumerate(blockchain):
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index-1]):
                return False

            if not cls.valid_proof(block.trax[:-1], block.previous_hash, block.proof):
                print('Proof of work is invalid')
                return False
        return True

    @staticmethod
    def verify_trax(transaction, get_balance, check_funds=True):
        if check_funds == True:
            sender_balance = get_balance(transaction.tx_sender)
            return sender_balance >= transaction.tx_amount and Wallet.verify_traxSign(transaction)
        else:
            return Wallet.verify_traxSign(transaction)

    @classmethod
    def verify_allTrax(cls, open_trax, get_balance):
        return all([cls.verify_trax(el,get_balance, False) for el in open_trax])