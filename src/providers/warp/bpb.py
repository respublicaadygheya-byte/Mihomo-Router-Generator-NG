import csv
from pathlib import Path


BPB_RESULT = Path(
    "/opt/BPB-Warp-Scanner/bin/BPB-Warp-Scanner-linux-amd64/result.csv"
)


def parse_endpoint(value):
    value = value.strip()

    # IPv6: [2606:4700:...]:8319
    if value.startswith("["):
        host, port = value.rsplit("]:", 1)
        return host[1:], int(port)

    # IPv4: 188.114.98.22:5956
    host, port = value.rsplit(":", 1)

    return host, int(port)


def scan_bpb():

    if not BPB_RESULT.exists():
        print(
            f"[WARP BPB] result.csv not found: {BPB_RESULT}"
        )
        return []

    nodes = []

    try:

        with open(
            BPB_RESULT,
            encoding="utf-8",
            newline=""
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:

                endpoint = row.get("Endpoint")

                if not endpoint:
                    continue

                try:

                    server, port = parse_endpoint(
                        endpoint
                    )

                    loss = float(
                        row["Loss rate"]
                        .replace("%", "")
                        .strip()
                    )

                    latency = int(
                        row["Avg. Latency"]
                        .replace("ms", "")
                        .strip()
                    )

                except (ValueError, KeyError):

                    continue

                # Полностью мёртвые endpoints
                # отбрасываем.
                # Остальные отдаём существующему checker.py.
                if loss >= 100:
                    continue

                nodes.append(
                    {
                        "server": server,
                        "port": port,
                        "mode": "wireguard",
                        "bpb_latency": latency,
                        "bpb_loss": loss,
                    }
                )

    except OSError as e:

        print(
            f"[WARP BPB] Failed to read result.csv: {e}"
        )

        return []

    nodes.sort(
        key=lambda x: (
            x["bpb_loss"],
            x["bpb_latency"]
        )
    )

    return nodes
