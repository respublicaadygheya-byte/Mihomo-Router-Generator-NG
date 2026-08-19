import json
from .register import get_or_register_masque
from .scanner import scan_endpoints
from .checker import check_masque
from ..config import WARP_MASQUE_OUTPUT_FILE

class MasqueProvider:
    def generate_nodes(self):
        account = get_or_register_masque()
        if not account:
            print("[WARP] No account registered, skipping")
            return []

        candidates = scan_endpoints(account)
        print(f"[WARP] Testing {len(candidates)} candidates with real connection checks...")

        nodes = []
        # Ограничим максимальное количество проверяемых за раз для скорости, но сделаем выборку большой (например, 40-50 штук)
        import random
        test_batch = random.sample(candidates, min(45, len(candidates)))

        for target in test_batch:
            node = {
                "name": f"[WARP WG] {target['server']}:{target['port']}",
                "type": "wireguard",
                "server": target["server"],
                "port": target["port"],
                "ip": account["assigned_ipv4"],
                "ipv6": account.get("assigned_ipv6", ""),
                "private-key": account["private_key"],
                "public-key": account["peer_public_key"],
                "reserved": account.get("reserved", [0,0,0])[:3],
                "udp": True,
                "mtu": 1280,
                "remote-dns-resolve": True
            }

            print(f"[WARP] Checking {target['server']}:{target['port']}...")
            checked = check_masque(node)

            if checked:
                nodes.append(checked)
                print(f"[WARP] OK -> {target['server']}:{target['port']} ({checked.get('latency')} ms)")
            else:
                print(f"[WARP] FAIL -> {target['server']}:{target['port']}")

            # Если набрали достаточно живых нод, можно остановиться (например, хватит 10-15 хороших)
            if len(nodes) >= 15:
                print("[WARP] Target amount of working nodes reached.")
                break

        nodes.sort(key=lambda x: x.get("latency", 9999))
        
        WARP_MASQUE_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(WARP_MASQUE_OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(nodes, f, indent=2, ensure_ascii=False)

        print(f"[WARP] Saved {len(nodes)} working nodes to {WARP_MASQUE_OUTPUT_FILE}")
        return nodes

if __name__ == "__main__":
    nodes = MasqueProvider().generate_nodes()
    print(f"Done: generated {len(nodes)} working WARP nodes.")
