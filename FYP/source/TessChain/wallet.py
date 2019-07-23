from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import PKCS1_v1_5
from Cryptodome.Hash import SHA256
import Cryptodome.Random as rand
import binascii

class Wallet:
    def __init__(self, node_id):
        self.private_key = None
        self.public_key = None
        self.node_id = node_id
 
    def binToAscii(self, key):
        """
        Converts the binary key to ASCII 
        """
        return binascii.hexlify(key.exportKey(format= 'DER')).decode('ascii') 
    
    def generate_keys(self):
        private_key = RSA.generate(1024, rand.new().read)
        public_key = private_key.publickey()
        return (self.binToAscii(private_key), self.binToAscii(public_key))

    def create_keys(self):
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key
        try:
            with open('wallet-{}.txt'.format(self.node_id), mode = 'w') as f:
                f.write(public_key)
                f.write('\n')
                f.write(private_key)
            return True
        except (IOError, IndexError):
            print('Saving wallet failed...')
            return False

    def load_keys(self):
        try:
            with open('wallet-{}.txt'.format(self.node_id), mode = 'r') as f:
                keys = f.readlines()
                public_key = keys[0][:-1]
                private_key = keys[1]
                self.public_key = public_key
                self.private_key = private_key
            return True
        except (IOError, IndexError):
            print('Loading wallet failed...')
            return False

    def sign_trax(self, sender, recipient, amount):
        signer = PKCS1_v1_5.new(RSA.import_key(binascii.unhexlify(self.private_key)))
        h = SHA256.new((str(sender)+str(recipient)+str(amount)).encode('utf8'))

        signature = signer.sign(h)
        return binascii.hexlify(signature).decode('ascii')


    @staticmethod
    def verify_traxSign(trax):
        public_key = RSA.import_key(binascii.unhexlify(trax.tx_sender))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA256.new((str(trax.tx_sender)+str(trax.tx_recipient)+str(trax.tx_amount)).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(trax.signature))