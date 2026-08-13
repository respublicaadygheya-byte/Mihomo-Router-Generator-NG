import json
import os
import base64
from typing import Dict, Any, Optional

from .config import WARP_ACCOUNT_FILE, WARP_CACHE_DIR


def generate_keypair():
    """
    Временный генератор ключей.
    Реальную регистрацию Cloudflare добавим после проверки pipeline.
    """
    private = base64.b64encode(os.urandom(32)).decode()
    public = base64.b64encode(os.urandom(32)).decode()

    return private, public


def get_or_register_account() -> Optional[Dict[str, Any]]:
    """
    Читает существующий аккаунт или создаёт тестовый.
    """

    WARP_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if WARP_ACCOUNT_FILE.exists():
        with open(WARP_ACCOUNT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)


    private_key, public_key = generate_keypair()

    account = {
        "private_key": private_key,
        "peer_public_key": "bmXOC+F1MicA0XYAsUVWa84CWxUbF+CThxvJjc6622U=",
        "ipv4": "172.16.0.2",
        "ipv6": "",
        "reserved": [0, 0, 0],
        "account_id": "test"
    }


    with open(WARP_ACCOUNT_FILE, "w", encoding="utf-8") as f:
        json.dump(account, f, indent=2)


    print("[WARP] Created local test account")

    return account
