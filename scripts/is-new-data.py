import json
import random

import requests as rq

text = rq.get('https://hermit-crab.neocities.org/winrate-data.js').text
# with open('winrate-data.js') as f:
#     text = f.read()

facets = json.loads(text.split('(', 1)[1][:-1])
ofinterest = random.choice(facets)
print('at:', ofinterest['_url'])
theirdata = json.loads(rq.get(ofinterest['_url']).text)

if json.dumps(ofinterest['rates']) == json.dumps(theirdata['rates']):
    print('no updates')
else:
    print('refreshed!')
