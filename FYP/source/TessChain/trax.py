from collections import OrderedDict
from utility.printable import Printable

class Trax(Printable):
    def __init__(self, tx_sender, tx_recipient, signature, tx_amount):
        self.tx_sender = tx_sender
        self.tx_recipient = tx_recipient
        self.signature = signature
        self.tx_amount = tx_amount

    def to_ordered_dict(self):
        return OrderedDict([('tx_sender', self.tx_sender), ('tx_recipient', self.tx_recipient), ('tx_amount', self.tx_amount)])