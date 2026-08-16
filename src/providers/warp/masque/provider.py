import json

from .checker import check_masque
from .register import get_or_register_masque
from .scanner import scan_endpoints
from ..config import WARP_MASQUE_OUTPUT_FILE


class MasqueProvider:

    def generate_nodes(self):
        account = get_or_register_masque()

        if not account:
            print("[WARP MASQUE] No account, skipping")
            return []

        candidates = scan_endpoints(account)

        print(
            f"[WARP MASQUE] "
            f"Testing {len(candidates)} endpoint candidates..."
        )

        nodes = []

        for target in candidates:
            node = {
                "name": (
                    f"[WARP MASQUE] "
                    f"{target['server']}:{target['port']}"
                ),

                "type": "masque",
                "provider": "warp",
                "protocol": "masque",

                "server": target["server"],
                "port": target["port"],

                "private-key": account["private_key"],
                "public-key": account["peer_public_key"],

                "ip": account["assigned_ipv4"],
                "ipv6": account.get("assigned_ipv6", ""),

                "uri": "https://cloudflareaccess.com",
                "sni": "consumer-masque.cloudflareclient.com",

                "mtu": 1280,
                "udp": True,
                "network": "quic",
                "remote-dns-resolve": True,
            }

            print(
                f"[WARP MASQUE] "
                f"Checking {target['server']}:{target['port']}..."
            )

            checked = check_masque(node)

            if checked:
                nodes.append(checked)

                print(
                    f"[WARP MASQUE] OK "
                    f"{target['server']}:{target['port']} "
                    f"({checked.get('latency')} ms)"
                )
            else:
                print(
                    f"[WARP MASQUE] FAIL "
                    f"{target['server']}:{target['port']}"
                )

        nodes.sort(
            key=lambda x: x.get("latency", 9999)
        )

        WARP_MASQUE_OUTPUT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            WARP_MASQUE_OUTPUT_FILE,
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
            f"[WARP MASQUE] "
            f"Saved {len(nodes)} nodes to "
            f"{WARP_MASQUE_OUTPUT_FILE}"
        )

        return nodes


if __name__ == "__main__":
    nodes = MasqueProvider().generate_nodes()

    print(
        f"Done: generated {len(nodes)} MASQUE nodes."
    )
