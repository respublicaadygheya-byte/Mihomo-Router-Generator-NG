import json
import base64
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import requests

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
)

from .config import (
    WARP_ACCOUNT_FILE,
    WARP_CACHE_DIR,
)

BASE_URL = "https://api.cloudflareclient.com/v0i1909051800"


def generate_keys():
    private = X25519PrivateKey.generate()
    public = private.public_key()

    private_key = base64.b64encode(
        private.private_bytes_raw()
    ).decode()

    public_key = base64.b64encode(
        public.public_bytes(
            Encoding.Raw,
            PublicFormat.Raw,
        )
    ).decode()

    return private_key, public_key


def is_account_valid(account: Dict[str, Any]) -> bool:
    """Проверяет наличие и непустоту всех критических полей аккаунта."""
    required = [
        "private_key",
        "peer_public_key",
        "token",
        "device_id",
        "server",
        "port",
        "ipv4",
    ]
    return all(
        key in account and account[key]
        for key in required
    )


def register_account() -> Dict[str, Any]:
    private_key, public_key = generate_keys()
    install_id = str(uuid.uuid4())

    payload = {
        "install_id": install_id,
        "tos": datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "key": public_key,
        "fcm_token": "",
        "type": "ios",
        "locale": "en_US",
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "okhttp/4.9.3",
    }

    print("[WARP] Registering Cloudflare account")

    try:
        r = requests.post(
            f"{BASE_URL}/reg",
            json=payload,
            headers=headers,
            timeout=20,
        )
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if r.status_code == 429:
            raise RuntimeError(
                "[WARP] Cloudflare API rate limit reached (429)"
            ) from e
        raise
    data = r.json()

    if not data.get("success"):
        raise RuntimeError(f"Registration failed: {data}")

    result = data["result"]
    device_id = result["id"]
    token = result["token"]

    print(f"[WARP] Registered device {device_id}")

    # Включаем WARP для созданного устройства
    r = requests.patch(
        f"{BASE_URL}/reg/{device_id}",
        json={"warp_enabled": True},
        headers={
            **headers,
            "Authorization": f"Bearer {token}",
        },
        timeout=20,
    )
    r.raise_for_status()

    result = r.json()["result"]
    peer = result["config"]["peers"][0]
    endpoint = peer["endpoint"]
    interface = result["config"]["interface"]

    # Предохранитель для формата v4 адреса
    raw_v4 = endpoint.get("v4", "")
    server = raw_v4.split(":")[0] if raw_v4 else ""
    if not server:
        raise RuntimeError(f"Invalid endpoint format from Cloudflare: {endpoint}")

    # Порт из API с fallback
    port = 2408
    if "ports" in endpoint and endpoint["ports"]:
        port = endpoint["ports"][0]

    # Cloudflare WARP client_id является Base64-кодированным
    # значением WireGuard reserved (3 байта).
    client_id = result["config"].get("client_id", "")

    if client_id:
        try:
            reserved = list(
                base64.b64decode(
                    client_id,
                    validate=True
                )
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to decode Cloudflare client_id: {e}"
            ) from e

        if len(reserved) != 3:
            raise RuntimeError(
                f"Invalid WARP reserved length: {len(reserved)}"
            )
    else:
        # Fallback для альтернативного формата ответа API.
        reserved = (
            result["config"].get("reserved")
            or interface.get("reserved")
            or [0, 0, 0]
        )

    print(f"[WARP] Reserved: {reserved}")

    account = {
        "private_key": private_key,
        "peer_public_key": peer["public_key"],
        "endpoint": endpoint.get("host", ""),
        "server": server,
        "port": port,
        "ipv4": interface["addresses"]["v4"],
        "ipv6": interface["addresses"].get("v6", ""),
        "account_id": result["account"]["id"],
        "device_id": device_id,
        "token": token,
        "ttl": result["account"].get("ttl"),
        "reserved": reserved,
    }

    return account


def get_or_register_account() -> Optional[Dict[str, Any]]:
    WARP_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if WARP_ACCOUNT_FILE.exists():
        try:
            with open(WARP_ACCOUNT_FILE, "r", encoding="utf-8") as f:
                account = json.load(f)
            if is_account_valid(account):
                return account
            print("[WARP] Cached account is invalid or incomplete. Re-registering...")
        except Exception as e:
            print(f"[WARP] Error reading account cache: {e}. Re-registering...")

    account = register_account()

    with open(WARP_ACCOUNT_FILE, "w", encoding="utf-8") as f:
        json.dump(account, f, indent=2)

    print("[WARP] Account saved successfully")
    return account
