Data refreshment process is setup as such:
- Cron job runs `periodic.sh` once a day. It does all the needful.

Manual process is done like so:
- To get the data: `update-data.py myresultfile.js`
- Uploaded manually or via: `upload.sh myresultfile.js winrates-data.js`

Envitonment variables: `NEOCITIES_APIKEY`

Extraction script python requirements: `requests, lxml, cssselect`