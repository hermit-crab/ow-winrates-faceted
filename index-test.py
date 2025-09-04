import re
import time
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

TEST_JS = '''() => {
    const ana = document.querySelector('.hero-name[title="Ana"]').parentElement;
    if (!ana) return "no Ana";
    const plotElem = ana.querySelector('.plot-wr');
    const svgPoints = plotElem.querySelectorAll('.plot-wr svg > g.cartesianlayer > g > g.overplot > g > g > g.trace.scatter > g.points > path:nth-child(1)');
    if (svgPoints.length != 3) return `svgPoints (${svgPoints.length}) != 3`;
    if (plotElem._fullData.length != 3 || plotElem._fullData[0].length < 2) return "odd data";
    if ((Date.now()/1000 - rawData[0]._ts)/60/60 > 24) return "stale data";
}'''
LOCAL = False
URL = 'https://hermit-crab.github.io/ow-winrates-faceted/'
if LOCAL:
    URL = Path(__file__).resolve().parent.joinpath('index.html').as_uri()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    if LOCAL:
        page.add_init_script(script='localStorage.uselocal="1"')
    page.route(re.compile('simpleanalytic'), lambda route: route.abort())
    js_errors = []
    page.on('pageerror', lambda e: js_errors.append(e))
    page.goto(URL, wait_until='load')
    time.sleep(1)
    ret = page.evaluate(TEST_JS)
    browser.close()
    assert js_errors == [], f'Errors: {js_errors}'
    assert not ret, f'Test failed: {ret}'
    print('passed')
