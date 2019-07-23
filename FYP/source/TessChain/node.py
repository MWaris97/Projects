from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from blockchain import Blockchain
from wallet import Wallet

from argparse import ArgumentParser

app = Flask(__name__)
CORS(app)


@app.route('/', methods = ['GET'])
def get_node_ui():
    return send_from_directory('ui', 'node.html')


@app.route('/network', methods = ['GET'])
def get_network_ui():
    return send_from_directory('ui', 'network.html')


@app.route('/wallet', methods = ['POST'])
def create_keys():
    if wallet.create_keys():
        global blockchain 
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201

    else:
        response = {
            'message': 'saving the keys failed'
        }
        return jsonify(response), 500


@app.route('/wallet', methods = ['GET'])
def load_keys():
    if wallet.load_keys():
        global blockchain 
        blockchain = Blockchain(wallet.public_key, port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201

    else:
        response = {
            'message': 'loading the keys failed'
        }
        return jsonify(response), 500

@app.route('/balance', methods = ['GET'])
def get_balance():
    balance = blockchain.get_balance()
    if balance != None:
        response = {
            'message': 'Fetched balance succesfully',
            'balance': balance
        }
        return jsonify(response), 200
    else:
        response = {
            'message': 'Loading balance failed',
            'wallet_set_up' : wallet.public_key != None
        }
        return jsonify(response), 500


@app.route('/broadcast_trax', methods = ['POST'])
def broadcast_trax():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    required = ['tx_sender', 'tx_recipient', 'tx_amount', 'signature']
    if not all(key in values for key in required):
        response = {
            'message': 'Some data is missing.'
        }
        return jsonify(response), 400
    
    success = blockchain.add_trax(values['tx_recipient'], 
    values['tx_sender'], values['signature'], 
    values['tx_amount'], is_recieving = True)

    if success:
        response = {
            'message' : 'Successfully added trasaction',
            'transaction':{
                'tx_sender': values['tx_sender'],
                'tx_recipient': values['tx_recipient'],
                'tx_amount': values['tx_amount'],
                'signature': values['signature']
            }
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Adding transaction failed'
        }
        return jsonify(response), 500


@app.route('/broadcast_block', methods = ['POST'])
def broadcast_block():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    if 'block' not in values:
        response = {
            'message': 'Some data is missing.'
        }
        return jsonify(response), 400
    block = values['block']
    if block['index'] == blockchain.chain[-1].index + 1:
        if blockchain.add_block(block):
            response = {'message': 'Block added'}
            return jsonify(response), 201
        else:
            response = {'message': 'Block seems invalid'}
            return jsonify(response), 409

    elif block['index'] > blockchain.chain[-1].index:
        #local blockchain is shorter
        response = {
            'message' : 'Blockchain seems to differ from local blockchain.'
        }
        blockchain.resolve_conflicts = True
        return jsonify(response), 200
    else:
        # Peer node's blochcain is shorter than ours
        response = {
            'message' : 'Blockchain seems to be shorter, block not added'
        }
        return jsonify(response), 409


@app.route('/transaction', methods = ['POST'])
def add_transaction():
    if wallet.public_key == None:
        response = {
            'message': 'No wallet set up'
        }
        return jsonify(response), 400

    values = request.get_json()

    if not values:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    required_fields = ['tx_recipient', 'tx_amount']
    if not all (field in values for field in required_fields):
        response = {
            'message': 'Required data is missing'
        }
        return jsonify(response), 400

    recipient = values['tx_recipient']
    amount = values['tx_amount']

    signature = wallet.sign_trax(wallet.public_key, recipient, amount)
    success = blockchain.add_trax(recipient, wallet.public_key, signature, amount)
    
    if success:
        response = {
            'message' : 'Successfully added trasaction',
            'transaction':{
                'tx_sender': wallet.public_key,
                'tx_recipient': recipient,
                'tx_amount': amount,
                'signature': signature
            },
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Adding transaction failed'
        }
        return jsonify(response), 500


@app.route('/mine', methods = ['POST'])
def mine():
    if blockchain.resolve_conflicts:
        response = {
            'message': 'Resolve conflicts first, block not added!'
        }
        return jsonify(response), 409
    block = blockchain.mine_block()
    if block != None:
        # redundancy in code, convert to funtion
        dict_block = block.__dict__.copy()
        dict_block['trax'] = [tx.__dict__ for tx in dict_block['trax']]  
        response = {
            'message': 'Block added succesfully',
            'block': dict_block,
            'funds': blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Adding a block failed.',
            'wallet_set_up': wallet.public_key != None
        }
        return jsonify(response), 500


@app.route('/resolve_conflicts', methods = ['POST'])
def resolve_conflicts():
    replaced = blockchain.resolve()
    
    if replaced:
        response = {'message': 'Chain was replaced'}
    else:
        response = {'message': 'Local chain kept'}

    return jsonify(response), 200


@app.route('/transactions', methods = ['GET'])
def get_open_trax():
    transactions = blockchain.get_open_trax()
    dict_trax = [tx.__dict__ for tx in transactions]
    return jsonify(dict_trax), 200


@app.route('/chain', methods = ['GET'])
def get_chain():
    chain_snapshot = blockchain.chain
    # redundancy in code, convert to funtion
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]

    for dict_block in dict_chain:
        dict_block['trax'] = [tx.__dict__ for tx in dict_block['trax']]

    return jsonify(dict_chain), 200


@app.route('/node', methods = ['POST'])
def add_node():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data attached'
        }
        return jsonify(response), 400
    
    if 'node' not in values:
        response = {
            'message': 'No node data found'
        }
        return jsonify(response), 400

    # can add wallet check here
    node = values['node']
    blockchain.add_peer_node(node)
    response = {
        'message': 'Node added succesfully',
        'all_nodes': blockchain.get_peer_nodes()
    }
    return jsonify(response), 201


@app.route('/node/<node_url>', methods = ['DELETE'])
def remove_node(node_url):
    if node_url == '' or node_url == None or node_url not in blockchain.get_peer_nodes():
        response = {
            'message': 'No node found.'
        }
        return jsonify(response), 400
    blockchain.remove_peer_node(node_url)
    response = {
        'message': 'Node removed',
        'all_nodes': blockchain.get_peer_nodes()
    }
    return jsonify(response), 200


@app.route('/nodes', methods = ['GET'])
def get_nodes():
    nodes = blockchain.get_peer_nodes()
    response = {
        'all_nodes': nodes
    }
    return jsonify(response), 200


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type = int, default = 5000)
    args = parser.parse_args()
    port = args.port

    wallet = Wallet(port)
    blockchain = Blockchain(wallet.public_key, port)

    app.run(host= '0.0.0.0', port= port)