import json
from pathlib import Path


HISTORY_FILE = Path(
    "cache/providers/warp-history.json"
)


def fingerprint(node):
    return json.dumps(
        node,
        sort_keys=True,
        ensure_ascii=False
    )


def load_history():
    if not HISTORY_FILE.exists():
        return []

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except Exception as e:
        print(
            f"[WARP-HISTORY] Failed to load history: {e}"
        )
        return []


def save_history(nodes):

    HISTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            nodes,
            f,
            indent=2,
            ensure_ascii=False
        )


def merge_warp_history(current):

    history = load_history()

    result = []
    seen = set()

    for node in history + current:

        fp = fingerprint(node)

        if fp in seen:
            continue

        seen.add(fp)
        result.append(node)

    save_history(result)

    return result
