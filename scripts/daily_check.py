#!/usr/bin/env python3
import json
import re
import time

import requests as rq

LOG_URL = 'https://hermit-crab.neocities.org/winrate-data-updatelog.txt'
DATA_URL = 'https://hermit-crab.neocities.org/winrate-data.js'

log = rq.get(LOG_URL).text.replace('\r', '\n').splitlines()
badlines = [l for l in log if re.search(r'(?i)==x|err|excep|traceb', l)]
badlines = [l for l in badlines if not re.search(r'mmr=Champion|juedou', l)] # juedou = stadium
if badlines:
    print('update log issues:\n' + '\n'.join([f'    > {l}' for l in badlines]))

now = time.time()
data = json.loads(rq.get(DATA_URL).text[6:-1])
sites = {'blizzard.com', 'blizzard.cn', 'nexon.com'}
found = set()
for site in sites:
    for facet in data:
        age_hours = (now - facet['_ts'])/60/60
        if site in facet['_url']:
            found.add(site)
            if age_hours > 24:
                print(f'stale data, {site}, {int(age_hours)} hours')
                break
missing = sites - found
if missing:
    print(f'no data for: {missing}')

print('-------------------------')
