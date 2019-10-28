import requests
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('-p', '--port', type = int, default = 5000)
args = parser.parse_args()
port = args.port

node = 'http://localhost:%'.format(port)

r = requests.post(node+'/node_wallet')
print(r)