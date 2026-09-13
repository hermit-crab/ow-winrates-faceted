Data refreshment process is setup as such:
- Cron runs the following job once a day. It does all the needful.
- `PYTHONUNBUFFERED=1 NEOCITIES_APIKEY=XXX CLEAR_CACHE=1 SKIP_CACHE_READ=1 RETRY=1 python scripts/periodic.py`

Simplest manual process is done as such:
- Get raw data: `python scripts/fetch_main_site.py main-data.raw.json`
- Convert to jsonp: `python scripts/combine_jsonp.py main-data.raw.json winrate-data.js`
    - `combine_jsonp` accepts multiple source files if you pulled other sources.
- At that point `index.html` can see the `winrate-data.js` alongside it (given `localStorage.uselocal="1"` was set).
- If needed uploaded manually or via: `NEOCITIES_APIKEY=XXX python scripts/upload.py myresultfile.js winrate-data.js`

Required python dependencies: `pip install requests lxml cssselect`