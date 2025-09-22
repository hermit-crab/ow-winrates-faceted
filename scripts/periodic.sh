cd "$(dirname "$0")"/..
mkdir -p archive

dt=`date '+%Y-%m-%d_%H'`
logfile="archive/update.${dt}.log"

# Archiving
cp winrate-data.js "archive/winrate-data.${dt}.js"
cp cache/main.html "archive/main.${dt}.html"
cp cache/index-cn.json "archive/index-cn.${dt}.json"
rm -r cache.bak
mv cache cache.bak

echo Extracting...
for i in 1 2; do
    date -Iseconds >> $logfile
    python scripts/update-data.py winrate-data.js >> $logfile 2>&1
    exitcode=$?
    [ $exitcode -eq 0 -o $i -eq 2 ] && break
    echo "==> fail, retrying soon" | tee -a $logfile
    sleep 3600
    rm -r cache
done

echo Uploading log...
scripts/upload.sh $logfile winrate-data-updatelog.txt > /dev/null
[ $exitcode -ne 0 ] && exit $exitcode
echo Uploading...
scripts/upload.sh winrate-data.js winrate-data.js > /dev/null
