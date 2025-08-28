import hashlib
import json
import os
import time

import requests as rq
from tqdm import tqdm

params = {
    'map': ['all-maps'],
    'role': ['All'],
    'rq': ['0', '2'], # 0=QP; 2=Comp; 1=?
    'input': ['Console', 'PC'],
    'region': ['Americas', 'Asia', 'Europe'],
    'tier': ['All', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster'],
}
base_url = 'https://overwatch.blizzard.com/en-us/rates/data/'
cache_dir = 'cache'
os.makedirs(cache_dir, exist_ok=True)

def combinations(params, parents=None):
    parents = parents or []
    name, vals = params[0]
    for val in vals:
        new_parents = [*parents, (name, val)]
        if not params[1:]:
            yield new_parents
        else:
            yield from combinations(params[1:], parents=new_parents)

facets = []
for combo in tqdm(list(combinations(list(params.items()))), 'Loading data...'):
    url = base_url + '?' + '&'.join(f'{k}={v}' for k, v in combo)
    key = 'owwr.' + hashlib.md5(url.encode('utf8')).hexdigest() + '.json'
    cache_fpath = os.path.join(cache_dir, key)
    if ('rq', '0') in combo and ('tier', 'All') not in combo:
        continue
    if os.path.exists(cache_fpath):
        with open(cache_fpath) as f:
            data = f.read()
    else:
        data = rq.get(url).text
        with open(cache_fpath, 'w') as f:
            f.write(data)
        pass
    facets.append((combo, json.loads(data)))

with open('winrate-data.js', 'w') as f:
    f.write('const DATA=' + json.dumps([time.time()] + [facet[1] for facet in facets]))
