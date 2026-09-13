#!/usr/bin/env python3
import hashlib
import json
from itertools import chain

from utils import cli_load_and_store, combinations, get

BASE_URL_CN = 'https://webapi.blizzard.cn/ow-armory-server'


def crawl_cn_site():
    index = json.loads(get(BASE_URL_CN + '/index', 'index-cn.json')[0])
    season = index['data']['seasons'][0]['id']
    print(f'Season: {season}')
    assert int(season) == max(int(s['id']) for s in index['data']['seasons'])
    params = {
        'game_mode': ['kuaisu', 'jingji'], # qp, comp
        'season': [season],
        'mmr': ['-127', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Emerald', 'Diamond', 'Master', 'Grandmaster', 'Champion']
    }
    params_stadium = {
        'game_mode': ['juedou'], # stadium
        'season': [season],
        'mmr': ['-127', 'Rookie', 'Novice', 'Contender', 'Elite', 'Pro', 'AllStar', 'Legend']
    }

    facets = []
    rqs = []
    for combo in chain(combinations(params), combinations(params_stadium)):
        rqs.append((combo, BASE_URL_CN + '/hero_leaderboard?' + '&'.join(f'{k}={v}' for k, v in combo)))

    for n, (combo, url) in enumerate(rqs, 1):
        print(f'\r{n}/{len(rqs)} Loading data...', end='')
        key = 'owwr-cn.' + hashlib.md5(url.encode('utf8')).hexdigest() + '.json'
        data, ts, _ = get(url, key)
        data = json.loads(data)
        if data['code'] != 0:
            print('\n==x bad data', url, data)
            continue
        if not data['data']:
            print('\n==x no data', url, data)
        data['_url'] = url
        data['_ts'] = ts
        data['_season'] = season
        facets.append(data)

    return facets


if __name__ == '__main__':
    cli_load_and_store(crawl_cn_site)
