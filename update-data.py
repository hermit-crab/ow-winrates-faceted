import hashlib
import json
import os
import traceback
from itertools import product

import requests as rq
from lxml import html

base_url =  'https://overwatch.blizzard.com/en-us/rates'
cache_dir = 'cache'
os.makedirs(cache_dir, exist_ok=True)

def get(url, cache_name):
    cache_fpath = os.path.join(cache_dir, cache_name)
    if os.path.exists(cache_fpath):
        with open(cache_fpath) as f:
            return f.read(), os.stat(cache_fpath).st_mtime
    else:
        rp = rq.get(url)
        rp.raise_for_status()
        text = rp.text
        assert text, f'empty body at {rp}'
        with open(cache_fpath, 'w') as f:
            f.write(text)
        return text, None

try:
    tree = html.fromstring(get(base_url, 'main.html')[0])
    form = tree.cssselect('form.herostats-filters')[0]
    selects = []
    for select in form.cssselect('select'):
        label = select.attrib['data-label']
        selects.append([label, []])
        for option in select.cssselect('option'):
            opt_label = option.attrib['data-title']
            opt_val = option.attrib['value']
            selects[-1][1].append((opt_label, opt_val))
    print(f'Selects: {selects}')
    selects = dict([(k, dict(opts)) for k, opts in selects])
    modes = [selects['rq']['Quick Play - Role Queue'], selects['rq']['Competitive - Role Queue']]
    print(f'Modes: {modes}')
except Exception:
    print('==x HTML parse failure')
    traceback.print_exc()
    # Sometimes Comp is on 1 for a few days. At first both 1 and 2 were available (
    # with 2 having seemingly older data and 1 having new season data).
    modes = ['0', '2'] # 0=QP; 2=Comp;

params = {
    'map': ['all-maps'],
    'role': ['All'],
    'rq': modes,
    'input': ['Console', 'PC'],
    'region': ['Americas', 'Asia', 'Europe'],
    'tier': ['All', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster'],
}

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
    rqs.append((combo, base_url + '/data/?' + '&'.join(f'{k}={v}' for k, v in combo)))

for n, (combo, url) in enumerate(rqs, 1):
    print(f'\r{n}/{len(rqs)} Loading data...', end='')
    key = 'owwr.' + hashlib.md5(url.encode('utf8')).hexdigest() + '.json'
    data, cache_ts = get(url, key)
    if cache_ts:
        cache_hits += 1
    data = json.loads(data)
    if isinstance(data, list) and not data:
        print('==x no data for', url)
        continue
    expected = sorted(combo)
    reported = sorted(data['selected'].items())
    if expected != reported:
        print(f'==x unexpected selection reported, expected:\n{expected}\ngot:\n{reported}')
    data['_url'] = url
    data['_ts'] = cache_ts
    facets.append((combo, data))

print(f'\nCache hits: {cache_hits}/{len(rqs)}')

with open('winrate-data.js', 'w') as f:
    f.write('jsonp(' + json.dumps([facet[1] for facet in facets]) + ')')
