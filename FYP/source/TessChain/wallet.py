from Cryptodome.PublicKey import RSA
from Cryptodome.Signature import PKCS1_v1_5
from Cryptodome.Hash import SHA256
from Cryptodome.Cipher import PKCS1_OAEP
import Cryptodome.Random as rand
import Cryptodome as crypto
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

    def create_keys(self, validator = True):
        private_key, public_key = self.generate_keys()
        self.private_key = private_key
        self.public_key = public_key

        if validator:
            try:
                with open('wallet-{}.txt'.format(self.node_id), mode = 'w') as f:
                    f.write(public_key)
                    f.write('\n')
                    f.write(private_key)
                return True
            except (IOError, IndexError):
                print('Saving wallet failed...')
                return False
        return True

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

    def sign_ballot(self, voterId, voter_key, voter_prik, candidate, vote):
        signer = PKCS1_v1_5.new(RSA.import_key(binascii.unhexlify(voter_prik)))
        h = SHA256.new((str(voterId)+str(voter_key)+str(candidate)+str(vote)).encode('utf8'))

        signature = signer.sign(h)
        return binascii.hexlify(signature).decode('ascii')


    @staticmethod
    def verify_ballotSign(ballot):
        public_key = RSA.import_key(binascii.unhexlify(ballot.voter_key))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA256.new((str(ballot.voterId)+str(ballot.voter_key)+str(ballot.candidate)+str(ballot.vote)).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(ballot.signature))

        
    @staticmethod
    def encrypt_voterId(voterId, voter_key):
        public_key = RSA.import_key(binascii.unhexlify(voter_key))
        encryptor = PKCS1_OAEP.new(public_key)
        encrypted_voterId = encryptor.encrypt(bytes(voterId, 'utf8'))
        return binascii.hexlify(encrypted_voterId).decode('ascii')


    @staticmethod
    def decrypt_voterId(encrypted_voterId, voter_prik):
        private_key = RSA.import_key(binascii.unhexlify(voter_prik))
        decryptor = PKCS1_OAEP.new(private_key)
        decrypted_voterId = decryptor.decrypt(binascii.unhexlify(encrypted_voterId))
        return str(decrypted_voterId, 'utf8')
