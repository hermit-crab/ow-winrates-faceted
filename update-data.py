import hashlib
import json
import os
from itertools import product

import requests as rq
from tqdm import tqdm

params = {
    'map': ['all-maps'],
    'role': ['All'],
    'rq': ['0', '1'], # 0=QP; 1=Comp; 2=?
    'input': ['Console', 'PC'],
    'region': ['Americas', 'Asia', 'Europe'],
    'tier': ['All', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster'],
}
base_url = 'https://overwatch.blizzard.com/en-us/rates/data/'
cache_dir = 'cache'
os.makedirs(cache_dir, exist_ok=True)

def combinations(params):
    keys = list(params.keys())
    for values in product(*params.values()):
        yield list(zip(keys, values))

facets = []
cache_hits = 0
rqs = []
for combo in combinations(params):
    if ('rq', '0') in combo and ('tier', 'All') not in combo:
        continue
    rqs.append((combo, base_url + '?' + '&'.join(f'{k}={v}' for k, v in combo)))
for combo, url in tqdm(rqs, 'Loading data...'):
    key = 'owwr.' + hashlib.md5(url.encode('utf8')).hexdigest() + '.json'
    cache_fpath = os.path.join(cache_dir, key)
    if os.path.exists(cache_fpath):
        cache_hits += 1
        with open(cache_fpath) as f:
            data = f.read()
    else:
        data = rq.get(url).text
        with open(cache_fpath, 'w') as f:
            f.write(data)
    data = json.loads(data)
    if isinstance(data, list) and not data:
        print('==x no data for', url)
        continue
    expected = sorted(combo)
    reported = sorted(data['selected'].items())
    if expected != reported:
        print(f'==x unexpected selection reported, expected:\n{expected}\ngot:\n{reported}')
    data['_url'] = url
    data['_ts'] = os.stat(cache_fpath).st_mtime
    facets.append((combo, data))

print(f'Cache hits: {cache_hits}/{len(rqs)}')

with open('winrate-data.js', 'w') as f:
    f.write('jsonp(' + json.dumps([facet[1] for facet in facets]) + ')')
