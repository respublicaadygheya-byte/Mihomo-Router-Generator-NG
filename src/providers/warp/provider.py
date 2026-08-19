import json
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

        candidates = scan_endpoints(account)


        print(
            f"[WARP] Scanned: {len(candidates)} endpoints"
        )



        all_nodes = history.copy()



        for target in candidates:


            node = {

                "name":
                    f"[WARP] Auto {target['server']}",

                "type":
                    "wireguard",

                "provider":
                    "warp",

                "protocol":
                    "wireguard",

                "server":
                    target["server"],

                "port":
                    target["port"],

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


        nodes.extend(history)



        unique = {}

        for n in nodes:

            key = (
                n["server"],
                n.get("protocol"),
                n.get("amnezia-wg-option", {}).get("jc")
            )

            if key in unique:

                merged = unique[key].copy()

                for k, v in n.items():

                    if v not in (None, ""):
                        merged[k] = v

                unique[key] = merged

            else:

                unique[key] = n



        nodes = list(
            unique.values()
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
