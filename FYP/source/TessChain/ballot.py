from collections import OrderedDict
from utility.printable import Printable

class Ballot(Printable):
    def __init__(self, voter_key, candidate, signature, vote):
        self.voter_key = voter_key
        self.candidate = candidate
        self.signature = signature
        self.vote = vote

    def to_ordered_dict(self):
        return OrderedDict([('voter_key', self.voter_key), ('candidate', self.candidate), ('vote', self.vote)])