#!/bin/bash
set -e

export PATH=/usr/local/go/bin:/usr/local/bin:/usr/bin:/bin

cd /root/Mihomo-Router-Generator-NG

echo "========================================"
echo "MIHOMO AUTO UPDATE"
echo "========================================"
echo "Started: $(date)"

./update.sh

echo
echo "Checking generated YAML..."

test -s publish/mihomo.yaml
test -s publish/openclash.yaml

echo "YAML files OK"

echo "Checking secrets..."

if grep -R "private-key\\|private_key" publish; then
    echo "ERROR: WARP private key detected in publish!"
    exit 1
fi

echo "No secrets detected"

git add -f publish/mihomo.yaml publish/openclash.yaml

if git diff --cached --quiet; then
    echo "No changes to publish."
else
    git commit -m "Auto-update Mihomo configs: $(date '+%Y-%m-%d %H:%M:%S')"
    git push origin main
    echo "GitHub push completed."
fi

echo "Finished: $(date)"
echo "========================================"
