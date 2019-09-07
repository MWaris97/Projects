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


@app.route('/node_wallet', methods = ['POST'])
def create_node_keys():
    if wallet.create_keys():
        global node_key, node_prik
        node_key = wallet.public_key
        node_prik = wallet.private_key
        global blockchain 
        blockchain = Blockchain(node_key, port)
        response = {
            'public_key': node_key,
            'private_key': node_prik,
        }
        return jsonify(response), 201

    else:
        response = {
            'message': 'saving the keys failed'
        }
        return jsonify(response), 500


@app.route('/node_wallet', methods = ['GET'])
def load_node_keys():
    if wallet.load_keys():
        global node_key, node_prik
        node_key = wallet.public_key
        node_prik = wallet.private_key
        global blockchain 
        blockchain = Blockchain(node_key, port)
        response = {
            'public_key': node_key,
            'private_key': node_prik,
        }
        return jsonify(response), 201

    else:
        response = {
            'message': 'loading the keys failed'
        }
        return jsonify(response), 500


@app.route('/wallet', methods = ['POST'])
def create_keys():
    if wallet.create_keys(False):
        global voter_key, voter_prik
        voter_key = wallet.public_key
        voter_prik = wallet.private_key
        res = mine(voter_key)
        response = {
            'public_key': voter_key,
            'private_key': voter_prik,
            'vote_available': blockchain.get_balance(voter_key),
            'res': res
        }
        return jsonify(response), 201

    else:
        response = {
            'message': 'saving the keys failed'
        }
        return jsonify(response), 500

@app.route('/balance', methods = ['GET'])
def get_balance():
    global voter_key
    balance = blockchain.get_balance(voter_key) #needs fixing
    if balance != None:
        response = {
            'message': 'Fetched balance succesfully',
            'balance': balance
        }
        return jsonify(response), 200
    else:
        response = {
            'message': 'Loading balance failed',
            'wallet_set_up' : wallet.public_key != None #needs fixing
        }
        return jsonify(response), 500


@app.route('/broadcast_ballot', methods = ['POST'])
def broadcast_ballot():
    values = request.get_json()
    if not values:
        response = {
            'message': 'No data found'
        }
        return jsonify(response), 400
    required = ['voter_key', 'candidate', 'vote', 'signature']
    if not all(key in values for key in required):
        response = {
            'message': 'Some data is missing.'
        }
        return jsonify(response), 400
    
    success = blockchain.add_ballot(values['candidate'], 
    values['voter_key'], values['signature'], 
    values['vote'], is_recieving = True)

    if success:
        response = {
            'message' : 'Successfully added trasaction',
            'ballot':{
                'voter_key': values['voter_key'],
                'candidate': values['candidate'],
                'vote': values['vote'],
                'signature': values['signature']
            }
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Adding ballot failed'
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


@app.route('/ballot', methods = ['POST'])
def add_ballot():
    if voter_key == None:
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
    required_fields = ['candidate', 'vote']
    if not all (field in values for field in required_fields):
        response = {
            'message': 'Required data is missing'
        }
        return jsonify(response), 400

    candidate = values['candidate']
    vote = values['vote']

    signature = wallet.sign_ballot(voter_key, voter_prik, candidate, vote)
    success = blockchain.add_ballot(candidate, voter_key, signature, vote)
    
    if success:
        res = mine(voter_key)
        response = {
            'message' : 'Successfully added trasaction',
            'ballot':{
                'voter_key': voter_key,
                'candidate': candidate,
                'vote': vote,
                'signature': signature
            },
            'vote_available': blockchain.get_balance(),
            'res': res
        }
        return jsonify(response), 201
    else:
        response = {
            'message': 'Adding ballot failed'
        }
        return jsonify(response), 500


# @app.route('/mine', methods = ['POST'])
def mine(voter_key):
    if blockchain.resolve_conflicts:
        # response = {
        #     'message': 'Resolve conflicts first, block not added!'
        # }
        # return jsonify(response), 409
        blockchain.resolve()
    block = blockchain.mine_block(voter_key)
    if block != None:
        # redundancy in code, convert to funtion
        dict_block = block.__dict__.copy()
        dict_block['ballot'] = [bt.__dict__ for bt in dict_block['ballot']]  
        response = {
            'message': 'Block added succesfully',
            'block': dict_block,
            'vote_available': blockchain.get_balance(voter_key)
        }
        return response
    else:
        response = {
            'message': 'Adding a block failed.',
            'wallet_set_up': node_key != None
        }
        return response


# @app.route('/resolve_conflicts', methods = ['POST'])
# def resolve_conflicts():
#     replaced = blockchain.resolve()
    
#     if replaced:
#         response = {'message': 'Chain was replaced'}
#     else:
#         response = {'message': 'Local chain kept'}

#     return jsonify(response), 200


@app.route('/ballots', methods = ['GET'])
def get_open_ballots():
    ballots = blockchain.get_open_ballots()
    dict_ballots = [bt.__dict__ for bt in ballots]
    return jsonify(dict_ballots), 200


@app.route('/chain', methods = ['GET'])
def get_chain():
    chain_snapshot = blockchain.chain
    # redundancy in code, convert to funtion
    dict_chain = [block.__dict__.copy() for block in chain_snapshot]

    for dict_block in dict_chain:
        dict_block['ballot'] = [bt.__dict__ for bt in dict_block['ballot']]

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