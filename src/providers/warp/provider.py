import json
from datetime import datetime, timezone
from typing import List, Dict, Any


from .config import (
    WARP_OUTPUT_FILE,
    PROVIDERS_CACHE_DIR,
)


from .register import get_or_register_account
from .scanner import scan_endpoints
from .checker import check_warp
from .awg_profiles import AWG_PROFILES



MAX_NODES = 100



def add_awg(node, profile):

    node["amnezia-wg-option"] = profile.copy()

    return node



class WarpProvider:


    def generate_nodes(self):


        account = get_or_register_account()


        if not account:
            return []



        history_file = PROVIDERS_CACHE_DIR / "warp-history.json"


        history = []


        if history_file.exists():

            with open(history_file, encoding="utf-8") as f:
                history = json.load(f)



        print(
            f"[WARP] History: {len(history)} nodes"
        )


        nodes = []


        for item in history:

            node = item.copy()

            node.setdefault(
                "source",
                "history"
            )


            if "name" not in node:
                node["name"] = (
                    f"[WARP] History {node['server']}"
                )

            node["history"] = True


            checked = check_warp(node)


            if checked:

                checked["last_seen"] = (
                    datetime.now(timezone.utc)
                    .isoformat()
                )

                nodes.append(checked)


                print(
                    "[WARP HISTORY KEEP]",
                    checked["server"],
                    checked.get("port"),
                    checked.get("latency")
                )


        from collections import Counter

        print()
        print("=== AFTER HISTORY LOAD ===")
        print("TOTAL:", len(nodes))

        print(
            Counter(
                n.get("source", "UNKNOWN")
                for n in nodes
            )
        )

        print(
            "HISTORY MARKED:",
            sum(
                1 for n in nodes
                if n.get("history")
            )
        )


        candidates = scan_endpoints()


        print(
            f"[WARP] Scanned: {len(candidates)} endpoints"
        )



        for target in candidates:


            node = {

                "name":
                    f"[WARP] Auto {target['server']}",

                "type":
                    "wireguard",

                "provider":
                    "warp",

                "protocol":
                    target.get(
                        "protocol",
                        "wireguard"
                    ),

                "server":
                    target["server"],

                "port":
                    target["port"],

                "source":
                    target.get(
                        "source",
                        "scanner"
                    ),

                "ip":
                    account["ipv4"],

                "public-key":
                    account["peer_public_key"],

                "private-key":
                    account["private_key"],

                "reserved":
                    account.get(
                        "reserved",
                        [0,0,0]
                    ),

                "udp": True,

                "mtu":1280,

            }



            if account.get("ipv6"):
                node["ipv6"] = account["ipv6"]



            if target.get("mode") == "amnezia":

                for profile in AWG_PROFILES:

                    awg_node = node.copy()

                    awg_node = add_awg(
                        awg_node,
                        profile
                    )

                    awg_node["protocol"] = "amnezia-wg"

                    awg_node["source"] = target.get(
                        "source",
                        "scanner"
                    )

                    awg_node["name"] = (
                        f"[WARP] AWG {target['server']} jc{profile['jc']}"
                    )

                    checked = check_warp(awg_node)

                    if checked:

                        nodes.append(checked)

                        print(
                            "[WARP AWG KEEP]",
                            awg_node["server"],
                            profile["jc"],
                            checked.get("latency")
                        )

                continue


                node["name"] = (
                    f"[WARP] AWG {target['server']}"
                )



            checked = check_warp(node)


            if checked:

                nodes.append(checked)

                print(
                    "[WARP] KEEP",
                    node["server"],
                    checked.get("latency")
                )




        from collections import Counter

        print()
        print("=== BEFORE DEDUP SOURCE ===")

        print(
            Counter(
                n.get("source", "UNKNOWN")
                for n in nodes
            )
        )

        print()
        print("=== BEFORE DEDUP TOTAL ===")
        print(len(nodes))


        print()
        print("=== DEDUP INPUT STATS ===")

        print(
            "TOTAL:",
            len(nodes)
        )

        print(
            "HISTORY:",
            sum(
                1 for n in nodes
                if n.get("history")
            )
        )


        unique = {}

        duplicate_stats = {}
        history_duplicate_stats = {}

        for n in nodes:

            key = (
                n.get("server"),
                n.get("port"),
                n.get("type"),
                n.get("protocol"),
                n.get("amnezia-wg-option", {}).get("jc")
            )

            if key in unique:

                old = unique[key]

                old_source = old.get("source", "unknown")
                new_source = n.get("source", "unknown")

                pair = tuple(
                    sorted(
                        (
                            old_source,
                            new_source
                        )
                    )
                )

                duplicate_stats[pair] = (
                    duplicate_stats.get(pair, 0) + 1
                )

                old_history = bool(
                    old.get("history")
                )

                new_history = bool(
                    n.get("history")
                )

                if old_history or new_history:

                    history_pair = (
                        "history" if old_history else "new",
                        "history" if new_history else "new",
                    )

                    history_duplicate_stats[
                        history_pair
                    ] = (
                        history_duplicate_stats.get(
                            history_pair,
                            0
                        ) + 1
                    )

                merged = old.copy()

                for k, v in n.items():

                    if v not in (None, ""):
                        merged[k] = v

                unique[key] = merged

            else:

                unique[key] = n



        dedup_removed = len(nodes) - len(unique)

        nodes = list(
            unique.values()
        )


        print()
        print("=== DEDUP OUTPUT STATS ===")

        print(
            "TOTAL:",
            len(nodes)
        )

        print(
            "HISTORY:",
            sum(
                1 for n in nodes
                if n.get("history")
            )
        )

        print(
            "REMOVED:",
            dedup_removed
        )


        print()
        print("=== DUPLICATE SOURCE STATS ===")

        for pair, count in sorted(
            duplicate_stats.items()
        ):
            print(
                pair,
                count
            )

        print(
            "TOTAL DUPLICATES:",
            sum(duplicate_stats.values())
        )


        print()
        print("=== HISTORY DUPLICATE STATS ===")

        for pair, count in sorted(
            history_duplicate_stats.items()
        ):
            print(
                pair,
                count
            )

        print(
            "HISTORY DUPLICATES:",
            sum(
                history_duplicate_stats.values()
            )
        )


        awg_nodes = [
            n for n in nodes
            if n.get("protocol") == "amnezia-wg"
        ]


        warp_nodes = [
            n for n in nodes
            if n.get("protocol") != "amnezia-wg"
        ]


        warp_nodes.sort(
            key=lambda x:
            x.get(
                "latency",
                9999
            )
        )


        warp_nodes = warp_nodes[:MAX_NODES]


        nodes = warp_nodes + awg_nodes


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


        with open(
            history_file,
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
            f"[WARP] Saved {len(nodes)} nodes"
        )


        return nodes



if __name__ == "__main__":

    nodes = WarpProvider().generate_nodes()

    print(
        f"Done: generated {len(nodes)} WARP nodes."
    )
