import json
from pathlib import Path


HISTORY_FILE = Path(
    "cache/providers/warp-history.json"
)


def is_awg(node):

    server = str(node.get("server", ""))
    port = node.get("port")

    return (
        port == 500
        or "tribukvy" in server
    )


def node_id(node):

    if is_awg(node):

        server = node.get("server")

        if not server:
            return None

        return (
            "awg",
            server,
            node.get("port"),
        )


    name = node.get("name")
    server = node.get("server")

    if not name and not server:
        return None

    return (
        "warp",
        name,
        server,
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

            data = json.load(f)

            if isinstance(data, list):
                return data

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

    storage = {}


    for node in history:

        key = node_id(node)

        if key:
            storage[key] = node


    for node in current:

        key = node_id(node)

        if not key:
            continue


        if key in storage:

            merged = storage[key].copy()

            for k, v in node.items():

                if v not in (None, ""):
                    merged[k] = v

            storage[key] = merged

        else:

            storage[key] = node


    result = sorted(
        storage.values(),
        key=lambda x: (
            node_id(x)[0],
            str(node_id(x))
        )
    )


    save_history(result)

    return result
