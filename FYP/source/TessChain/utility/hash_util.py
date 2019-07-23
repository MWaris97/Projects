import hashlib as hl
import json

def hash_string_256(string):
    """Hashes the string and using hexdigest() it returns a binary string.

        Arguments:
            :block: The block that should be hashed
    """

    return hl.sha256(string).hexdigest()

def hash_block(block):
    """Hashes a block and returns a SHA256 hash of the block.
        uses JSON.dumps to convert the block (i.e in stored in a dictionary) in a string
        SHA256.hexdigest() returns a binary string.

        Arguments:
            :block: The block that should be hashed
    """
    hashable_block = block.__dict__.copy()
    hashable_block['trax'] = [tx.to_ordered_dict() for tx in hashable_block['trax']]
    return hash_string_256(json.dumps(hashable_block, sort_keys=True).encode())