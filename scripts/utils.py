import json
import os
import sys
import time
import traceback
from http.cookiejar import DefaultCookiePolicy
from itertools import product

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

CACHE_DIR = 'cache'

default_session = requests.Session()
default_session.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))
adapter = HTTPAdapter(max_retries=Retry(5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]))
default_session.mount('http://', adapter)
default_session.mount('https://', adapter)
_cache_message_printed = False
_do_cache_read = not os.environ.get('SKIP_CACHE_READ')
_do_cache_write = not os.environ.get('SKIP_CACHE_WRITE')
_cache_stats = [0, 0]


def get(url, cache_name, session=default_session):
    global _cache_message_printed
    if not _cache_message_printed and (not _do_cache_read or not _do_cache_write):
        print(f'read cache: {_do_cache_read}; write cache: {_do_cache_write};')
        _cache_message_printed = True

    _cache_stats[0] += 1
    cache_fpath = os.path.join(CACHE_DIR, cache_name)
    if _do_cache_read and os.path.exists(cache_fpath):
        _cache_stats[1] += 1
        with open(cache_fpath, encoding='utf8') as f:
            return f.read(), os.stat(cache_fpath).st_mtime, True
    else:
        rp = session.get(url)
        rp.raise_for_status()
        text = rp.text
        assert text, f'empty body at {rp}'
        os.makedirs(CACHE_DIR, exist_ok=True)
        mtime = time.time()
        if _do_cache_write:
            with open(cache_fpath, 'w', encoding='utf8') as f:
                f.write(text)
            mtime = os.stat(cache_fpath).st_mtime
        return text, mtime, False


def combinations(params):
    keys = list(params.keys())
    for values in product(*params.values()):
        yield list(zip(keys, values))


def cli_load_and_store(loader):
    if not sys.argv[1:]:
        raise Exception('specify output file as first argument')
    dest = sys.argv[1]
    retries = 1 if os.environ.get('RETRY') else 0

    for i in range(retries+1):
        try:
            output = loader()
            break
        except Exception:
            traceback.print_exc()
            if i < retries:
                print(f'==x loader {loader.__name__!r} fail, retrying in an hour')
                time.sleep(3600)
            else:
                print(f'==x loader {loader.__name__!r} fail, exiting')
                sys.exit(1)

    print(f'cache hits: {_cache_stats[1]}/{_cache_stats[0]}')
    print(f'==> {loader.__name__!r} success, storing in {dest}')
    with open(dest, 'w', encoding='utf8') as f:
        json.dump(output, f)


def combine_sources(target_fpaths, dest_fpath):
    print(f'==> combining {[t for t in target_fpaths]} as jsonp to {dest_fpath}')

    combined = []
    for target in target_fpaths:
        with open(target) as f:
            combined.extend(json.load(f))

    with open(dest_fpath, 'w', encoding='utf8') as f:
        f.write('jsonp(' + json.dumps(combined) + ')')


def upload(target, dest):
    apikey = os.environ.get('NEOCITIES_APIKEY')
    with open(target, 'rb') as f:
        rp = requests.post('https://neocities.org/api/upload', headers={'Authorization': f'Bearer {apikey}'}, files={dest: f})
        rp.raise_for_status()
        return rp
