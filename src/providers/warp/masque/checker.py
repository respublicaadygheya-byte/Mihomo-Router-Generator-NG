from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.request
import urllib.error

import yaml


BASE_DIR = Path(__file__).resolve().parents[4]
MIHOMO = BASE_DIR / "bin" / "mihomo.bin"

TEST_URL = "https://cloudflare.com/cdn-cgi/trace"
TEST_TIMEOUT = 8


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def check_masque(node):
    port = get_free_port()

    cfg = {
        "mixed-port": port,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "warning",

        "proxies": [node],

        "proxy-groups": [{
            "name": "TEST",
            "type": "select",
            "proxies": [node["name"]],
        }],

        "rules": [
            "MATCH,TEST"
        ],
    }

    cfg_path = None
    proc = None

    try:
        # --------------------------------------------------------------
        # Create temporary Mihomo config.
        # --------------------------------------------------------------

        with tempfile.NamedTemporaryFile(
            "w",
            suffix=".yaml",
            delete=False,
        ) as f:
            yaml.dump(
                cfg,
                f,
                allow_unicode=True,
                sort_keys=False,
            )
            cfg_path = f.name

        # --------------------------------------------------------------
        # Start Mihomo.
        # --------------------------------------------------------------

        proc = subprocess.Popen(
            [
                str(MIHOMO),
                "-f",
                cfg_path,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Give Mihomo time to initialize the proxy listener.
        time.sleep(2.5)

        if proc.poll() is not None:
            print(
                f"[WARP MASQUE CHECK] Mihomo exited immediately "
                f"for {node.get('server')}:{node.get('port')}"
            )
            return None

        # --------------------------------------------------------------
        # HTTP proxy -> Mihomo.
        # --------------------------------------------------------------

        proxy_support = urllib.request.ProxyHandler({
            "http": f"http://127.0.0.1:{port}",
            "https": f"http://127.0.0.1:{port}",
        })

        opener = urllib.request.build_opener(proxy_support)

        # --------------------------------------------------------------
        # Cloudflare trace is the actual WARP health check.
        #
        # We deliberately do NOT use:
        #
        #   http://cp.cloudflare.com/generate_204
        #
        # because Cloudflare may return an anti-bot challenge there.
        # That does not mean the MASQUE tunnel is broken.
        # --------------------------------------------------------------

        req = urllib.request.Request(
            TEST_URL,
            headers={
                "User-Agent": "curl/7.68.0",
                "Accept": "*/*",
            },
        )

        start = time.time()

        try:
            with opener.open(
                req,
                timeout=TEST_TIMEOUT,
            ) as resp:

                status = resp.status
                body = resp.read(4096).decode(
                    "utf-8",
                    errors="replace",
                )

        except urllib.error.HTTPError as e:
            status = e.code
            body = e.read(4096).decode(
                "utf-8",
                errors="replace",
            )

            print(
                f"[WARP MASQUE CHECK] HTTP {status} "
                f"{node.get('server')}:{node.get('port')}"
            )

            return None

        latency = round(
            (time.time() - start) * 1000,
            2,
        )

        # --------------------------------------------------------------
        # Validate Cloudflare trace response.
        # --------------------------------------------------------------

        if status != 200:
            print(
                f"[WARP MASQUE CHECK] FAIL "
                f"{node.get('server')}:{node.get('port')} "
                f"HTTP={status}"
            )
            return None

        trace = {}

        for line in body.splitlines():
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            trace[key.strip()] = value.strip()

        warp = trace.get("warp", "").lower()

        # --------------------------------------------------------------
        # The most important condition:
        #
        # Cloudflare must report warp=on.
        # --------------------------------------------------------------

        if warp != "on":
            print(
                f"[WARP MASQUE CHECK] FAIL "
                f"{node.get('server')}:{node.get('port')} "
                f"warp={warp or 'missing'}"
            )
            return None

        # --------------------------------------------------------------
        # Successful MASQUE/WARP node.
        # --------------------------------------------------------------

        result = {
            **node,
            "latency": latency,
        }

        print(
            f"[WARP MASQUE CHECK] OK "
            f"{node.get('server')}:{node.get('port')} "
            f"({latency} ms) "
            f"warp=on "
            f"loc={trace.get('loc', '-')}"
        )

        return result

    except Exception as e:
        print(
            f"[WARP MASQUE CHECK] ERROR "
            f"{node.get('server')}:{node.get('port')}: "
            f"{type(e).__name__}: {e}"
        )

    finally:
        # --------------------------------------------------------------
        # Stop Mihomo.
        # --------------------------------------------------------------

        if proc and proc.poll() is None:
            proc.kill()

            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

        # --------------------------------------------------------------
        # Remove temporary config.
        # --------------------------------------------------------------

        if cfg_path:
            Path(cfg_path).unlink(
                missing_ok=True
            )

    return None
