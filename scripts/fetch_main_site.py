#!/usr/bin/env python3
import hashlib
import json

import lxml.html
from utils import cli_load_and_store, combinations, get

BASE_URL =  'https://overwatch.blizzard.com/en-us/rates'


def crawl_main_site():
    try:
        tree = lxml.html.fromstring(get(BASE_URL, 'main.html')[0])
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
        modes = [
            selects['rq']['Quick Play - Role Queue'],
            selects['rq']['Competitive - Role Queue']
        ]
        # Sometimes Comp is on 1 for a few days. At first both 1 and 2 were available (
        # with 2 having seemingly older data and 1 having new season data).
        print(f'Modes: {modes}') # 0=QP; 2(or 1)=Comp;
        print(f'Tiers: {list(selects["tier"].values())}')
    except Exception:
        print('==x HTML parse failure')
        raise

    params = {
        'map': ['all-maps'],
        'role': ['All'],
        'rq': modes,
        'input': ['Console', 'PC'],
        'region': ['Americas', 'Asia', 'Europe'],
        'tier': ['All', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Emerald', 'Diamond', 'Master', 'Grandmaster'],
    }

    facets = []
    rqs = []
    for combo in combinations(params):
        if ('rq', '0') in combo and ('tier', 'All') not in combo:
            continue
        rqs.append((combo, BASE_URL + '/data/?' + '&'.join(f'{k}={v}' for k, v in combo)))

    for n, (combo, url) in enumerate(rqs, 1):
        print(f'\r{n}/{len(rqs)} Loading data...', end='')
        key = 'owwr.' + hashlib.md5(url.encode('utf8')).hexdigest() + '.json'
        data, ts, _ = get(url, key)
        data = json.loads(data)
        if isinstance(data, list) and not data:
            print('\n==x no data for', url)
            continue
        expected = sorted(combo)
        reported = sorted(data['rates']['selected'].items())
        if expected != reported:
            print(f'\n==x unexpected selection reported, expected:\n{expected}\ngot:\n{reported}')
            raise Exception
        data['_url'] = url
        data['_ts'] = ts
        facets.append(data)

    return facets


if __name__ == '__main__':
    cli_load_and_store(crawl_main_site)
