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

echo "[3/4] Split by categories"
python3 src/splitter.py cache/filtered/available.json cache/filtered/ru.json cache/filtered/foreign.json

RU_COUNT=$(jq '. | length' cache/filtered/ru.json 2>/dev/null || echo "0")
FOREIGN_COUNT=$(jq '. | length' cache/filtered/foreign.json 2>/dev/null || echo "0")
echo "  Russian: $RU_COUNT"
echo "  Foreign: $FOREIGN_COUNT"

echo "[4/4] Generate config"
python3 src/generator.py \
    --ru cache/filtered/ru.json \
    --foreign cache/filtered/foreign.json \
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
