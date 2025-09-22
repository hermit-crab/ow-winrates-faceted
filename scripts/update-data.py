#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import traceback
from http.cookiejar import DefaultCookiePolicy
from itertools import chain, product

import lxml.html
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL =  'https://overwatch.blizzard.com/en-us/rates'
BASE_URL_CN = 'https://webapi.blizzard.cn/ow-armory-server'
CACHE_DIR = 'cache'
os.makedirs(CACHE_DIR, exist_ok=True)

session = requests.Session()
session.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))
adapter = HTTPAdapter(max_retries=Retry(5, backoff_factor=1, backoff_jitter=1, status_forcelist=[429, 500, 502, 503, 504]))
session.mount('http://', adapter)
session.mount('https://', adapter)


def get(url, cache_name):
    cache_fpath = os.path.join(CACHE_DIR, cache_name)
    if os.path.exists(cache_fpath):
        with open(cache_fpath, encoding='utf8') as f:
            return f.read(), os.stat(cache_fpath).st_mtime, True
    else:
        rp = session.get(url)
        rp.raise_for_status()
        text = rp.text
        assert text, f'empty body at {rp}'
        with open(cache_fpath, 'w', encoding='utf8') as f:
            f.write(text)
        return text, os.stat(cache_fpath).st_mtime, False


def combinations(params):
    keys = list(params.keys())
    for values in product(*params.values()):
        yield list(zip(keys, values))


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
    except Exception:
        print('==x HTML parse failure')
        raise

    params = {
        'map': ['all-maps'],
        'role': ['All'],
        'rq': modes,
        'input': ['Console', 'PC'],
        'region': ['Americas', 'Asia', 'Europe'],
        'tier': ['All', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster'],
    }

    facets = []
    cache_hits = 0
    rqs = []
    for combo in combinations(params):
        if ('rq', '0') in combo and ('tier', 'All') not in combo:
            continue
        rqs.append((combo, BASE_URL + '/data/?' + '&'.join(f'{k}={v}' for k, v in combo)))

    for n, (combo, url) in enumerate(rqs, 1):
        print(f'\r{n}/{len(rqs)} Loading data...', end='')
        key = 'owwr.' + hashlib.md5(url.encode('utf8')).hexdigest() + '.json'
        data, ts, cached = get(url, key)
        if cached:
            cache_hits += 1
        data = json.loads(data)
        if isinstance(data, list) and not data:
            print('\n==x no data for', url)
            continue
        expected = sorted(combo)
        reported = sorted(data['selected'].items())
        if expected != reported:
            print(f'\n==x unexpected selection reported, expected:\n{expected}\ngot:\n{reported}')
            raise Exception
        data['_url'] = url
        data['_ts'] = ts
        facets.append((combo, data))

    print(f'\nCache hits: {cache_hits}/{len(rqs)}')
    return facets


def crawl_cn_site():
    index = json.loads(get(BASE_URL_CN + '/index', 'index-cn.json')[0])
    season = index['data']['seasons'][0]['id']
    params = {
        'game_mode': ['kuaisu', 'jingji'], # qp, comp
        'season': [season],
        'mmr': ['-127', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster', 'Champion']
    }
    params_stadium = {
        'game_mode': ['juedou'], # stadium
        'season': [season],
        'mmr': ['-127', 'Rookie', 'Novice', 'Contender', 'Elite', 'Pro', 'AllStar', 'Legend']
    }

    facets = []
    cache_hits = 0
    rqs = []
    for combo in chain(combinations(params), combinations(params_stadium)):
        rqs.append((combo, BASE_URL_CN + '/hero_leaderboard?' + '&'.join(f'{k}={v}' for k, v in combo)))

    for n, (combo, url) in enumerate(rqs, 1):
        print(f'\r{n}/{len(rqs)} Loading data...', end='')
        key = 'owwr-cn.' + hashlib.md5(url.encode('utf8')).hexdigest() + '.json'
        data, ts, cached = get(url, key)
        if cached:
            cache_hits += 1
        data = json.loads(data)
        if data['code'] != 0:
            print('\n==x bad data', url, data)
            continue
        if not data['data']:
            print('\n==x no data', url, data)
        data['_url'] = url
        data['_ts'] = ts
        data['_season'] = season
        facets.append((combo, data))

    print(f'\nCache hits: {cache_hits}/{len(rqs)}')
    return facets


def main():
    print('==> Main site')
    facets = crawl_main_site()
    try:
        print('==> CN site')
        facets.extend(crawl_cn_site())
    except Exception:
        print('==x CN crawl failure')
        traceback.print_exc()

    dest = sys.argv[1] if sys.argv[1:] else 'winrates-data.js'
    with open(dest, 'w', encoding='utf8') as f:
        f.write('jsonp(' + json.dumps([facet[1] for facet in facets]) + ')')


if __name__ == '__main__':
    main()
