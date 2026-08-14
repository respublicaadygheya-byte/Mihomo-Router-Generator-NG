import json
from typing import List, Dict, Any

from .config import (
    FALLBACK_WARP_SERVERS,
    WARP_OUTPUT_FILE,
    PROVIDERS_CACHE_DIR,
)

from .register import get_or_register_account


class WarpProvider:

    def generate_nodes(self) -> List[Dict[str, Any]]:

        account = get_or_register_account()

        if not account:
            print("[WARP] No account available")
            return []

        nodes = []

        for target in FALLBACK_WARP_SERVERS:

            server = (
                account["server"]
                if target.get("use_account_server")
                else target["server"]
            )

            port = (
                account.get("port", 2408)
                if target.get("use_account_server")
                else target.get("port", 2408)
            )

            node = {
                "name": f"[WARP] Cloudflare {target['name']}",
                "type": "wireguard",
                "server": server,
                "port": port,
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

            nodes.append(node)


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
            f"[WARP] Generated {len(nodes)} candidate nodes -> {WARP_OUTPUT_FILE}"
        )

        return nodes


if __name__ == "__main__":

    nodes = WarpProvider().generate_nodes()

    print(
        f"Done: generated {len(nodes)} WARP nodes."
    )
