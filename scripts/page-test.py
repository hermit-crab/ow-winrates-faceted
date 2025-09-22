#!/usr/bin/env python3
import re
from pathlib import Path

import requests as rq
from playwright.sync_api import sync_playwright

TEST_JS = '''async () => {
    const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    await sleep(1000);
    const ana = document.querySelector('.hero-name[title="Ana"]').parentElement;
    if (!ana) return "no Ana";
    let plotElem = ana.querySelector('.plot-parent.wr .plot');
    let svgPoints = plotElem.querySelectorAll('svg > g.cartesianlayer > g > g.overplot > g > g > g.trace.scatter > g.points > path:nth-child(1)');
    if (svgPoints.length != 3) return `svgPoints (${svgPoints.length}) != 3`;
    if (plotElem._fullData.length != 3 || plotElem._fullData[0].length < 2) return "odd data";
    if ((Date.now()/1000 - rawData[0]._ts)/60/60 > 24) return "stale data";

    UI.chinaOn.checked = true;
    UI.cnExtra.checked = true;
    confHandler.sync();
    await sleep(1000);
    plotElem = ana.querySelector('.plot-parent.kd .plot');
    svgPoints = plotElem.querySelectorAll('svg > g.cartesianlayer > g > g.overplot > g > g > g.trace.scatter > g.points > path:nth-child(1)');
    if (svgPoints.length != 1) return `svgPoints (${svgPoints.length}) != 1 (CN)`;
    if (plotElem._fullData.length != 1 || plotElem._fullData[0].length < 2) return "odd data (CN)";
}'''
LOCAL = False
URL = 'https://hermit-crab.github.io/ow-winrates-faceted/'
if LOCAL:
    URL = Path(__file__).resolve().parent.parent.joinpath('index.html').as_uri()
LOG_URL = 'https://hermit-crab.neocities.org/winrate-data-updatelog.txt'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    if LOCAL:
        page.add_init_script(script='localStorage.uselocal="1"')
    page.route(re.compile('simpleanalytic'), lambda route: route.abort())
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(e))
    page.goto(URL, wait_until='load')
    ret = page.evaluate(TEST_JS)
    browser.close()
    assert js_errors == [], f'Errors: {js_errors}'
    assert not ret, f'Test failed: {ret}'
    print('page passed')

if not LOCAL:
    log = rq.get(LOG_URL).text.replace('\r', '\n').splitlines()
    badlines = [f'    > {l}' for l in log if re.search(r'(?i)==x|err|excep|traceb', l)]
    if badlines:
        print('update log issues:\n' + '\n'.join(badlines))
