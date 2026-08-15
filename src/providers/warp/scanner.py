from itertools import product


NETWORKS = [
    "162.159.192.",
    "162.159.193.",
    "188.114.96.",
    "188.114.97.",
]


def generate_candidates(limit_per_network=32):
    result = []

    for net in NETWORKS:
        for i in range(1, limit_per_network + 1):
            result.append(
                {
                    "server": f"{net}{i}",
                    "port": 2408,
                }
            )

    return result


def scan_endpoints():
    """
    Возвращает список кандидатов.
    Реальная проверка происходит через Mihomo checker.
    """

    candidates = generate_candidates()

    print(
        f"[WARP SCANNER] Generated {len(candidates)} endpoints"
    )

    return candidates


if __name__ == "__main__":
    for endpoint in scan_endpoints():
        print(endpoint)
