def scan_endpoints(account):
    """
    Build MASQUE endpoint candidates exclusively from the endpoint
    information returned by Cloudflare during MASQUE enrollment.

    We deliberately do not brute-force Cloudflare IP ranges here.
    """

    server_v4 = account.get("endpoint_v4", "").strip()
    server_v6 = account.get("endpoint_v6", "").strip()
    ports = account.get("endpoint_ports") or []

    if not ports:
        print("[WARP MASQUE SCANNER] No endpoint ports returned by Cloudflare")
        return []

    candidates = []

    for port in ports:
        try:
            port = int(port)
        except (TypeError, ValueError):
            continue

        if not (1 <= port <= 65535):
            continue

        if server_v4:
            candidates.append({
                "server": server_v4,
                "port": port,
                "mode": "masque",
                "family": "ipv4",
            })

        if server_v6:
            candidates.append({
                "server": server_v6,
                "port": port,
                "mode": "masque",
                "family": "ipv6",
            })

    print(
        f"[WARP MASQUE SCANNER] "
        f"Cloudflare endpoints: IPv4={server_v4 or '-'}, "
        f"IPv6={server_v6 or '-'}"
    )
    print(
        f"[WARP MASQUE SCANNER] "
        f"Ports: {ports}"
    )
    print(
        f"[WARP MASQUE SCANNER] "
        f"Generated {len(candidates)} endpoint candidates"
    )

    return candidates
