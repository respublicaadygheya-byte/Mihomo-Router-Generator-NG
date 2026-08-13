from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]

WARP_CACHE_DIR = BASE_DIR / "cache" / "warp"
PROVIDERS_CACHE_DIR = BASE_DIR / "cache" / "providers"

WARP_ACCOUNT_FILE = WARP_CACHE_DIR / "account.json"
WARP_OUTPUT_FILE = PROVIDERS_CACHE_DIR / "warp.json"


WARP_ENDPOINTS = [
    {
        "name": "Cloudflare EU-1",
        "server": "162.159.192.1",
        "port": 2408,
    },
    {
        "name": "Cloudflare EU-2",
        "server": "162.159.192.2",
        "port": 2408,
    },
    {
        "name": "Cloudflare EU-3",
        "server": "162.159.193.1",
        "port": 2408,
    },
    {
        "name": "Cloudflare Anycast-1",
        "server": "188.114.96.1",
        "port": 2408,
    },
    {
        "name": "Cloudflare Anycast-2",
        "server": "188.114.97.1",
        "port": 2408,
    },
]


CLOUDFLARE_API_URL = (
    "https://api.cloudflareclient.com/v0i1909051800/reg"
)
