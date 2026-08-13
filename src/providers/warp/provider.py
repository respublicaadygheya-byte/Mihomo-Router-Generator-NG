import json
from typing import List, Dict, Any

from .config import (
    WARP_ENDPOINTS,
    WARP_OUTPUT_FILE,
    PROVIDERS_CACHE_DIR,
)

from .register import get_or_register_account


class WarpProvider:

    def __init__(self, endpoints=None):
        self.endpoints = endpoints or WARP_ENDPOINTS


    def generate_nodes(self) -> List[Dict[str, Any]]:

        account = get_or_register_account()

        if not account:
            print("[WARP] No account")
            return []


        nodes = []

        for idx, (host, port) in enumerate(self.endpoints, 1):

            node = {
                "name": f"[WARP] Cloudflare #{idx}",
                "type": "wireguard",
                "server": host,
                "port": port,

                "ip": account["ipv4"],

                "public-key": account["peer_public_key"],
                "private-key": account["private_key"],

                "reserved": account["reserved"],

                "udp": True,
                "mtu": 1280
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
            f"[WARP] Generated {len(nodes)} nodes"
        )

        return nodes



if __name__ == "__main__":

    provider = WarpProvider()

    nodes = provider.generate_nodes()

    print(
        f"Done: {len(nodes)}"
    )
