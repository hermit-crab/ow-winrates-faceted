#!/usr/bin/env python3
import hashlib
import json

import curl_cffi.requests
import lxml.html
from utils import cli_load_and_store, combinations, get

BASE_URL_KR = 'https://overwatch-api.nexon.com/HeroRate'


def crawl_kr_site():
    session = curl_cffi.requests.Session(impersonate='chrome')

    try:
        text = get('https://overwatch.nexon.com/hero/rate', 'main-kr.html', session=session)[0]
        tree = lxml.html.fromstring(text)
        state_script = tree.cssselect('script[id="__NUXT_DATA__"]')[0]
        init_state = json.loads(state_script.text)
        for i, val in enumerate(init_state):
            if '경쟁전 - 역할 고정' in str(val): # tr: "Competitive Play - Role Queue"
                break
        comp_rq_code = int(init_state[i-1])
    except Exception:
        print('==x index parse failure')
        raise

    params = {
        'map': ['all'],
        'role': ['all'],
        'rq': ['0', str(comp_rq_code)],
        'input': ['pc'],
        # 'input': ['console', 'pc'],
        # 'region': ['korea', 'americas', 'asia', 'europe'],
        'region': ['korea'],
        'rank': ['all', 'bronze', 'silver', 'gold', 'platinum', 'emerald', 'diamond', 'master', 'grandmaster'],
    }

    facets = []
    rqs = []
    for combo in combinations(params):
        if ('rq', '0') in combo and ('tier', 'all') not in combo:
            continue
        rqs.append((combo, BASE_URL_KR + '?' + '&'.join(f'{k}={v}' for k, v in combo)))

    for n, (combo, url) in enumerate(rqs, 1):
        print(f'\r{n}/{len(rqs)} Loading data...', end='')
        key = 'owwr-kr.' + hashlib.md5(url.encode('utf8')).hexdigest() + '.json'
        data, ts, _ = get(url, key, session=session)
        data = json.loads(data)
        if not data['data']['list']:
            print('\n==x no data for', url)
            continue
        data['_url'] = url
        data['_ts'] = ts
        facets.append(data)

    return facets


if __name__ == '__main__':
    cli_load_and_store(crawl_kr_site)
