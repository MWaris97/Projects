from time import time
from utility.printable import Printable

class Block(Printable):
    def __init__(self, index, previous_hash, trax, proof, time = time()):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = time
        self.trax = trax
        self.proof = proof

    # def __repr__(self):
    #     return '[Index: {}, Previous hash: {}, Timestamp: {}, Transactions {}, Proof: {}]'.format(
    #         self.index,self.previous_hash,self.trax,self.timestamp,self.proof)