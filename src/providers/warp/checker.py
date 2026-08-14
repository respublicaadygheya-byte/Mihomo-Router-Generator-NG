import socket
import subprocess
import tempfile
import time
from pathlib import Path

import requests
import yaml


BASE_DIR = Path(__file__).resolve().parents[3]
MIHOMO = BASE_DIR / "bin" / "mihomo.bin"

TEST_URL = "http://cp.cloudflare.com/generate_204"


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def check_warp(node):
    port = get_free_port()

    cfg = {
        "mixed-port": port,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "warning",
        "proxies": [node],
        "proxy-groups": [
            {
                "name": "TEST",
                "type": "select",
                "proxies": [node["name"]],
            }
        ],
        "rules": [
            "MATCH,TEST",
        ],
    }

    with tempfile.TemporaryDirectory() as tmp:
        cfg_file = Path(tmp) / "config.yaml"

        with open(cfg_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                cfg,
                f,
                allow_unicode=True,
                sort_keys=False,
            )

        proc = subprocess.Popen(
            [
                str(MIHOMO),
                "-d",
                tmp,
                "-f",
                str(cfg_file),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        try:
            deadline = time.time() + 5

            while time.time() < deadline:
                with socket.socket(
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                ) as s:
                    if s.connect_ex(("127.0.0.1", port)) == 0:
                        break

                time.sleep(0.1)
            else:
                return False

            proxy_url = f"http://127.0.0.1:{port}"

            response = requests.get(
                TEST_URL,
                proxies={
                    "http": proxy_url,
                    "https": proxy_url,
                },
                timeout=10,
            )

            return response.status_code in (200, 204)

        except Exception as exc:
            print(
                f"[WARP CHECK] "
                f"{node.get('name', 'UNKNOWN')}: {exc}"
            )
            return False

        finally:
            proc.terminate()

            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


if __name__ == "__main__":
    from .provider import WarpProvider

    nodes = WarpProvider().generate_nodes()

    for node in nodes:
        result = check_warp(node)

        print(
            f"{node['name']}: "
            f"{'OK' if result else 'FAIL'}"
        )
