import base64
import json
import os
import secrets
import urllib.error
import urllib.request
from datetime import datetime, timezone

from pathlib import Path

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec, x25519
except ImportError as e:
    raise RuntimeError(
        "Требуется пакет cryptography. "
        "Установите: python3 -m pip install cryptography"
    ) from e


BASE_DIR = Path(__file__).resolve().parents[4]

CACHE_DIR = BASE_DIR / "cache" / "warp"
CACHE_FILE = CACHE_DIR / "masque-account.json"

API_BASE = "https://api.cloudflareclient.com/v0a4471"
API_URL = API_BASE + "/reg"

CLIENT_VERSION = "a-6.35-4471"
USER_AGENT = "WARP for Android"


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def generate_throwaway_curve25519_public_key():
    """
    Exact analogue of warp-reg-gw generateRandomWgPubkey().

    This key exists only for the initial POST /reg.
    It is NOT the MASQUE private key.
    """
    private_key = x25519.X25519PrivateKey.generate()

    public_key = private_key.public_key()

    return b64(
        public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    )


def generate_masque_keypair():
    """
    Exact analogue of Go:

        ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    return private_key, public_key


def public_key_to_base64_pkix(public_key) -> str:
    """
    Exact analogue of:

        x509.MarshalPKIXPublicKey(pub)
    """
    der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return b64(der)


def private_key_to_base64_sec1(private_key) -> str:
    """
    Exact analogue of:

        x509.MarshalECPrivateKey(key)
    """
    der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return b64(der)


def edge_pem_to_base64_pkix(edge_key: str) -> str:
    """
    Go warp-reg-gw receives the edge public key as PEM and converts it to
    canonical Base64 PKIX DER using pemPublicKeyToBase64().
    """
    edge_key = edge_key.strip()

    # Normal API case: PEM.
    try:
        cert_or_key = serialization.load_pem_public_key(
            edge_key.encode("ascii")
        )

        if not isinstance(cert_or_key, ec.EllipticCurvePublicKey):
            raise ValueError(
                f"Unexpected edge public key type: {type(cert_or_key)!r}"
            )

        der = cert_or_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return b64(der)

    except Exception:
        pass

    # Compatibility: API may return Base64 DER directly.
    try:
        der = base64.b64decode(edge_key, validate=True)

        pub = serialization.load_der_public_key(der)

        if not isinstance(pub, ec.EllipticCurvePublicKey):
            raise ValueError(
                f"Unexpected edge public key type: {type(pub)!r}"
            )

        canonical_der = pub.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return b64(canonical_der)

    except Exception as e:
        raise ValueError(
            "Cloudflare edge public key is neither valid PEM nor "
            "Base64 DER"
        ) from e


def split_endpoint(value: str) -> str:
    """
    Equivalent to Go's net.SplitHostPort() fallback logic.

    Examples:
        162.159.198.2:443 -> 162.159.198.2
        [2606:4700::2]:443 -> 2606:4700::2
        162.159.198.2      -> 162.159.198.2
    """
    if not value:
        return ""

    value = value.strip()

    # [IPv6]:port
    if value.startswith("["):
        end = value.find("]")
        if end != -1:
            return value[1:end]

    # IPv4/hostname:port
    if value.count(":") == 1:
        host, port = value.rsplit(":", 1)
        if port.isdigit():
            return host

    # Bare IPv6
    return value.strip("[]")


def request_json(
    method: str,
    url: str,
    payload=None,
    token=None,
):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "CF-Client-Version": CLIENT_VERSION,
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = None
    if payload is not None:
        data = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")

            if not body:
                return {}

            return json.loads(body)

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")

        raise RuntimeError(
            f"Cloudflare API HTTP {e.code}: {body[:1200]}"
        ) from e

    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Cloudflare API connection failed: {e}"
        ) from e


def register_masque():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # STEP 1
    # POST /reg with temporary Curve25519 key.
    # ------------------------------------------------------------------

    print("[WARP MASQUE] Step 1/2: creating WARP device...")

    wg_public_key = generate_throwaway_curve25519_public_key()

    serial = secrets.token_hex(8)

    # Go uses:
    #
    # time.Now().Format("2006-01-02T15:04:05.000-07:00")
    #
    # Use the current local timezone rather than forcing Z.
    tos = datetime.now().astimezone().strftime(
        "%Y-%m-%dT%H:%M:%S.%f%z"
    )

    # Convert +0300 -> +03:00
    if len(tos) >= 5:
        tos = tos[:-2] + ":" + tos[-2:]

    register_payload = {
        "key": wg_public_key,
        "install_id": "",
        "fcm_token": "",
        "tos": tos,
        "model": "PC",
        "serial_number": serial,
        "os_version": "",
        "key_type": "curve25519",
        "tunnel_type": "wireguard",
        "locale": "en_US",
        "warp_enabled": True,
    }

    first = request_json(
        "POST",
        API_URL,
        register_payload,
    )

    # IMPORTANT:
    # Cloudflare returns the account object at TOP LEVEL.
    # There is no ["result"].
    reg_id = first.get("id", "")
    token = first.get("token", "")

    if not reg_id:
        raise RuntimeError(
            "Cloudflare registration response contains no id"
        )

    if not token:
        raise RuntimeError(
            "Cloudflare registration response contains no token"
        )

    print(f"[WARP MASQUE] Step 1 OK: id={reg_id}")

    # ------------------------------------------------------------------
    # STEP 2
    # PATCH /reg/{id} with ECDSA P-256 MASQUE key.
    # ------------------------------------------------------------------

    print("[WARP MASQUE] Step 2/2: enrolling ECDSA P-256 MASQUE key...")

    private_key, public_key = generate_masque_keypair()

    public_key_b64 = public_key_to_base64_pkix(public_key)

    enroll_payload = {
        "key": public_key_b64,
        "key_type": "secp256r1",
        "tunnel_type": "masque",
    }

    enroll_url = f"{API_URL}/{reg_id}"

    second = request_json(
        "PATCH",
        enroll_url,
        enroll_payload,
        token=token,
    )

    # Again: TOP LEVEL object, no "result".
    response_id = second.get("id", "")
    response_token = second.get("token", "")

    if response_id and response_id != reg_id:
        print(
            "[WARP MASQUE] Warning: API returned a different id: "
            f"{response_id}"
        )

    # Go deliberately keeps the token from step 1.
    # If API returns one here, it is useful for diagnostics, but we keep
    # the exact Go behaviour.
    account = second.get("account") or {}
    account_id = account.get("id", "")

    key_type = second.get("key_type", "")
    tunnel_type = second.get("tunnel_type", "")

    config = second.get("config") or {}

    # ------------------------------------------------------------------
    # Extract config.peers[0]
    # ------------------------------------------------------------------

    peers = config.get("peers") or []

    if not peers:
        raise RuntimeError(
            "MASQUE registration succeeded but API returned no "
            "config.peers"
        )

    peer = peers[0] or {}

    edge_public_key_raw = peer.get("public_key", "")

    if not edge_public_key_raw:
        raise RuntimeError(
            "MASQUE registration response contains no peer public key"
        )

    endpoint = peer.get("endpoint") or {}

    endpoint_v4 = split_endpoint(endpoint.get("v4", ""))
    endpoint_v6 = split_endpoint(endpoint.get("v6", ""))

    endpoint_ports = endpoint.get("ports") or []

    # Normalize ports to integers.
    endpoint_ports = [
        int(port)
        for port in endpoint_ports
        if str(port).isdigit()
    ]

    # ------------------------------------------------------------------
    # Extract config.interface.addresses
    # ------------------------------------------------------------------

    interface = config.get("interface") or {}
    addresses = interface.get("addresses") or {}

    assigned_ipv4 = addresses.get("v4", "")
    assigned_ipv6 = addresses.get("v6", "")

    # ------------------------------------------------------------------
    # Convert edge public key to canonical Base64 PKIX DER.
    # ------------------------------------------------------------------

    peer_public_key = edge_pem_to_base64_pkix(
        edge_public_key_raw
    )

    # ------------------------------------------------------------------
    # Serialize ECDSA credentials exactly like Go.
    # ------------------------------------------------------------------

    private_key_b64 = private_key_to_base64_sec1(
        private_key
    )

    public_key_b64 = public_key_to_base64_pkix(
        public_key
    )

    # ------------------------------------------------------------------
    # Final account object.
    #
    # This is the structure expected by the NG MASQUE provider.
    # ------------------------------------------------------------------

    account_data = {
        "id": response_id or reg_id,
        "token": token,
        "account": account_id,
        "key_type": key_type or "secp256r1",
        "tunnel_type": tunnel_type or "masque",

        "private_key": private_key_b64,
        "public_key": public_key_b64,

        "endpoint_v4": endpoint_v4,
        "endpoint_v6": endpoint_v6,
        "endpoint_ports": endpoint_ports,

        "peer_public_key": peer_public_key,

        "assigned_ipv4": assigned_ipv4,
        "assigned_ipv6": assigned_ipv6,
    }

    # Basic sanity checks before writing credentials.
    if not account_data["private_key"]:
        raise RuntimeError("Generated ECDSA private key is empty")

    if not account_data["public_key"]:
        raise RuntimeError("Generated ECDSA public key is empty")

    if not account_data["peer_public_key"]:
        raise RuntimeError("Edge public key is empty")

    if not account_data["endpoint_v4"] and not account_data["endpoint_v6"]:
        raise RuntimeError(
            "MASQUE registration returned no endpoint IPv4/IPv6"
        )

    if not account_data["endpoint_ports"]:
        raise RuntimeError(
            "MASQUE registration returned no endpoint ports"
        )

    # Save with restrictive permissions.
    tmp_file = CACHE_FILE.with_suffix(".json.tmp")

    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(
            account_data,
            f,
            indent=2,
            ensure_ascii=False,
        )
        f.write("\n")

    os.chmod(tmp_file, 0o600)
    os.replace(tmp_file, CACHE_FILE)

    print("[WARP MASQUE] Registration successful!")
    print(f"  ID:          {account_data['id']}")
    print(f"  Account:     {account_data['account']}")
    print(f"  Key type:    {account_data['key_type']}")
    print(f"  Tunnel type: {account_data['tunnel_type']}")
    print(f"  Endpoint v4: {account_data['endpoint_v4']}")
    print(f"  Endpoint v6: {account_data['endpoint_v6']}")
    print(f"  Ports:       {account_data['endpoint_ports']}")
    print(f"  Assigned v4: {account_data['assigned_ipv4']}")
    print(f"  Assigned v6: {account_data['assigned_ipv6']}")
    print(f"  Cache:       {CACHE_FILE}")

    return account_data


def get_or_register_masque():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                data = json.load(f)

            # Do not silently accept the old X25519 cache.
            required = (
                "id",
                "token",
                "private_key",
                "public_key",
                "peer_public_key",
                "endpoint_ports",
            )

            missing = [
                key
                for key in required
                if not data.get(key)
            ]

            if missing:
                raise ValueError(
                    "MASQUE cache is incomplete: "
                    + ", ".join(missing)
                )

            if data.get("tunnel_type") != "masque":
                raise ValueError(
                    "MASQUE cache has wrong tunnel_type: "
                    f"{data.get('tunnel_type')!r}"
                )

            if data.get("key_type") != "secp256r1":
                raise ValueError(
                    "MASQUE cache has wrong key_type: "
                    f"{data.get('key_type')!r}"
                )

            return data

        except Exception as e:
            print(
                "[WARP MASQUE] Existing cache is invalid: "
                f"{e}"
            )
            print(
                "[WARP MASQUE] A new MASQUE registration will be created."
            )

    return register_masque()
