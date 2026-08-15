NETWORKS = [
    "162.159.192.",
    "162.159.193.",
    "188.114.96.",
    "188.114.97.",
]


AMNEZIA_SERVERS = [
    "pl.tribukvy.ltd",
    "nl.tribukvy.ltd",
    "fi.tribukvy.ltd",
    "lv.tribukvy.ltd",
    "de.tribukvy.ltd",
    "ee.tribukvy.ltd",
    "ru0.tribukvy.ltd",

    "tel.pl.tribukvy.ltd",
    "tel.fi.tribukvy.ltd",
    "tel.de.tribukvy.ltd",
]


def generate_candidates():

    result = []


    # Cloudflare WARP WG
    for net in NETWORKS:
        for i in range(1, 33):
            result.append(
                {
                    "server": f"{net}{i}",
                    "port": 2408,
                    "mode": "wireguard",
                }
            )


    # AmneziaWG
    for server in AMNEZIA_SERVERS:
        result.append(
            {
                "server": server,
                "port": 500,
                "mode": "amnezia",
            }
        )


    return result



def scan_endpoints():

    candidates = generate_candidates()

    print(
        f"[WARP SCANNER] Generated {len(candidates)} endpoints"
    )

    return candidates



if __name__ == "__main__":

    for x in scan_endpoints():
        print(x)
