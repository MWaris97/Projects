import requests

node = 'http://localhost:2001'

for i in range(3101,3130):
    r = requests.post(node+'/wallet', json= {
        "voterId": "16CS{}".format(i)
    })

    re = requests.post(node+'/ballot', json={
        "candidate": "DEVOTE",
	    "vote": 1
    })