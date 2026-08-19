#!/bin/bash
set -e

echo "=============================="
echo "CLASH META ROUTER GENERATOR"
echo "=============================="

echo "[1/4] Import sources"
rm -rf cache/imported/* cache/filtered/*
mkdir -p cache/imported cache/filtered

python3 src/importer.py cache/imported/raw_proxies.txt
python3 src/parser.py cache/imported/raw_proxies.txt cache/imported/proxies.json

COUNT=$(jq '. | length' cache/imported/proxies.json 2>/dev/null || echo "0")
echo "  Proxy imported: $COUNT"

echo "[2/4] Check proxies"
python3 src/checker.py cache/imported/proxies.json cache/filtered/available.json

AVAIL=$(jq '. | length' cache/filtered/available.json 2>/dev/null || echo "0")
echo "  Working proxies: $AVAIL"

echo "[3/4] Generate WARP providers"

python3 -m src.providers.warp.provider

echo "[3/4] Generate WARP MASQUE providers"

python3 -m src.providers.warp.masque.provider

echo "[3/4] Merge proxy pool"

python3 src/merge_providers.py

POOL_COUNT=$(jq '. | length' cache/filtered/all.json 2>/dev/null || echo "0")
echo "  Proxy pool: $POOL_COUNT"

echo "[4/4] Generate config"
python3 src/generator.py \
    --proxies cache/filtered/all.json \
    --ru-direct domains:lists/ru_direct_domains.txt \
    --ru-direct ips:lists/ru_direct_ips.txt \
    --output publish/mihomo.yaml

echo "[5/5] Validate generated config with Mihomo"
python3 src/filter_mihomo.py \
    publish/mihomo.yaml \
    publish/mihomo-filtered.yaml

mv publish/mihomo-filtered.yaml publish/mihomo.yaml
cp publish/mihomo.yaml publish/openclash.yaml

echo "=============================="
echo "UPDATE COMPLETE"
echo "=============================="
ls -lh publish/

echo
echo "Checking Git changes..."

cd /root/Mihomo-Router-Generator-NG

git add -f publish/mihomo.yaml publish/openclash.yaml

if git diff --cached --quiet; then
    echo "No config changes detected."
else
    git commit -m "Auto-update Mihomo configs: $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
    echo "GitHub push completed."
fi

echo "Auto update finished: $(date)"
