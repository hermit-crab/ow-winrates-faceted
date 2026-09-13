import os
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

from utils import combine_sources, upload

os.chdir(Path(__file__).resolve().parent.parent)

# Archive previous run #########################################################

archive_path = 'archive/' + datetime.now().strftime('%Y-%m-%d_%H_%M')
os.makedirs(archive_path, exist_ok=True)

for fpath in [
    'output/winrate-data.js',
    'output/periodic.log',
    'cache/main.html',
    'cache/main-kr.html',
    'cache/index-cn.json',
]:
    if os.path.exists(fpath):
        shutil.copy(fpath, archive_path)

# Wipe output and cache ########################################################

os.makedirs('output', exist_ok=True)
for entry in os.scandir('output'):
    os.remove(entry)
main_logf = open('output/periodic.log', 'w', encoding='utf8')

def log(text):
    print(text)
    main_logf.write(text + '\n')
    main_logf.flush()

log(f'==> Archive at: {archive_path}')

if os.environ.get('CLEAR_CACHE'):
    log('==> Clearing cache')
    if os.path.exists('cache.bak'):
        shutil.rmtree('cache.bak')
    if os.path.exists('cache'):
        shutil.move('cache', 'cache.bak')
os.makedirs('cache', exist_ok=True)

# Run extractions ##############################################################

log('==> Extracting...')
sources = ['main', 'kr', 'cn']
jobs = {}
for name in sources:
    dest = f'output/{name}-data.raw.json'
    logf = open(f'output/{name}.log', 'w')
    proc = subprocess.Popen([sys.executable, f'scripts/fetch_{name}_site.py', dest], stdout=logf, stderr=logf)
    jobs[name] = {'process': proc, 'dest': dest, 'logf': logf}
log('==> Waiting completion...')
for i in range(3600*2):
    if all(p['process'].poll() is not None for p in jobs.values()):
        break
    time.sleep(1)

# Handle outputs ###############################################################

artifacts = []
for name, job in jobs.items():
    code = job['process'].returncode
    if code != 0:
        log(f'==x job {name!r}: bad returncode {code}')
    if not os.path.exists(job['dest']):
        log(f'==x job {name!r}: no artifact')
    else:
        artifacts.append(job['dest'])
    job['logf'].close()
    logf_fpath = job['logf'].name
    main_logf.write('==> Individual loader logs:\n')
    with open(logf_fpath) as f:
        sep = '='*10
        main_logf.write(f'{sep} {logf_fpath} {sep}\n{f.read()}\n')

# Upload #######################################################################

main_loader_success = jobs['main']['process'].returncode == 0
if not main_loader_success:
    log('==x main loader failed, wont combine or upload data')

if main_loader_success:
    combine_sources(artifacts, 'output/winrate-data.js')

def guard_upload(src, dst):
    if os.environ.get('SKIP_UPLOAD'):
        log(f'...skip upload: {src} -> {dst}')
        return
    try:
        upload(src, dst)
    except Exception:
        log(traceback.format_exc())
        raise

log('==> Uploading log...')
main_logf.flush()
guard_upload(main_logf.name, 'winrate-data-updatelog.txt')
if main_loader_success:
    log('==> Uploading dataset...')
    guard_upload('output/winrate-data.js', 'winrate-data.js')
    archived_fpath = os.path.join(archive_path, 'winrate-data.js')
    if os.path.exists(archived_fpath):
        log('==> Uploading backup...')
        guard_upload(archived_fpath, 'winrate-data.bak.js')

log('==> Done')
