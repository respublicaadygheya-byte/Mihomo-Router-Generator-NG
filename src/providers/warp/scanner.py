from .bpb import scan_bpb
from .native import generate_candidates


def scan_endpoints():

    candidates = []

    bpb_nodes = scan_bpb()

    if bpb_nodes:
        print(
            f"[WARP BPB] Loaded {len(bpb_nodes)} endpoints"
        )

        candidates.extend(bpb_nodes)


    native_nodes = generate_candidates()

    print(
        f"[WARP NATIVE] Loaded {len(native_nodes)} endpoints"
    )

    candidates.extend(native_nodes)


    return candidates


if __name__ == "__main__":

    for x in scan_endpoints():
        print(x)
