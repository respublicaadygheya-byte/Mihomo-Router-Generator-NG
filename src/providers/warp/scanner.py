from .bpb import scan_bpb
from .native import generate_candidates


def scan_endpoints():

    # Сначала используем BPB-Warp-Scanner.
    bpb_nodes = scan_bpb()

    if bpb_nodes:

        print(
            f"[WARP BPB] Loaded {len(bpb_nodes)} endpoints"
        )

        return bpb_nodes

    # Если BPB недоступен или result.csv пуст,
    # сохраняем старый fallback.
    candidates = generate_candidates()

    print(
        f"[WARP SCANNER] Generated {len(candidates)} endpoints"
    )

    return candidates


if __name__ == "__main__":

    for x in scan_endpoints():

        print(x)
