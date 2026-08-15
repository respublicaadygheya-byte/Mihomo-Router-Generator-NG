import json
from typing import List, Dict, Any

from .config import (
    WARP_OUTPUT_FILE,
    PROVIDERS_CACHE_DIR,
)

from .register import get_or_register_account
from .scanner import scan_endpoints
from .checker import check_warp


class WarpProvider:

    def generate_nodes(self) -> List[Dict[str, Any]]:

        account = get_or_register_account()

        if not account:
            print("[WARP] No account available")
            return []

        nodes = []

        endpoints = scan_endpoints()

        print(
            f"[WARP] Testing {len(endpoints)} candidates..."
        )

        for idx, target in enumerate(endpoints, start=1):

            node = {
                "name": (
                    f"[WARP] Auto-{idx} "
                    f"{target['server']}"
                ),
                "type": "wireguard",
                "server": target["server"],
                "port": target["port"],
                "ip": account["ipv4"],
                "public-key": account["peer_public_key"],
                "private-key": account["private_key"],
                "reserved": account.get(
                    "reserved",
                    [0, 0, 0]
                ),
                "udp": True,
                "mtu": 1280,
            }

            if account.get("ipv6"):
                node["ipv6"] = account["ipv6"]

            checked = check_warp(node)

            if checked:
                nodes.append(checked)

                print(
                    f"[WARP] KEEP: {checked['name']} "
                    f"{checked.get('latency')} ms"
                )

            else:
                print(
                    f"[WARP] DROP: {node['name']}"
                )


        nodes.sort(
            key=lambda x: x.get(
                "latency",
                9999
            )
        )

        print("[WARP] Sorted by latency:")
        for n in nodes:
            print(
                f"  {n['name']} "
                f"{n.get('latency')} ms"
            )

        PROVIDERS_CACHE_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            WARP_OUTPUT_FILE,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                nodes,
                f,
                indent=2,
                ensure_ascii=False
            )

        print(
            f"[WARP] Generated {len(nodes)} working nodes -> {WARP_OUTPUT_FILE}"
        )

        return nodes


if __name__ == "__main__":

    nodes = WarpProvider().generate_nodes()

    print(
        f"Done: generated {len(nodes)} WARP nodes."
    )
