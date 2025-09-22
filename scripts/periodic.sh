cd "$(dirname "$0")"/..
mkdir -p archive

dt=`date '+%Y-%m-%d_%H'`

# Archiving
cp winrate-data.js "archive/winrate-data.${dt}.js"
cp cache/main.html "archive/main.${dt}.html"
cp cache/index-cn.json "archive/index-cn.${dt}.json"
rm -r ./cache.bak
mv cache cache.bak

echo Extracting...
python scripts/update-data.py winrate-data.js > "archive/update.${dt}.log" 2>&1
exitcode=$?
echo Uploading log...
scripts/upload.sh "archive/update.${dt}.log" winrate-data-update.txt > /dev/null
[ $exitcode -ne 0 ] && exit $exitcode
echo Uploading...
scripts/upload.sh winrate-data.js winrate-data.js > /dev/null
