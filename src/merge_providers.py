import json
from pathlib import Path


AVAILABLE = Path("cache/filtered/available.json")
WARP = Path("cache/providers/warp.json")
OUTPUT = Path("cache/filtered/all.json")


def load_json(path):
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():

    proxies = []

    available = load_json(AVAILABLE)
    warp = load_json(WARP)

    proxies.extend(available)
    proxies.extend(warp)

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            proxies,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"Available: {len(available)}")
    print(f"WARP: {len(warp)}")
    print(f"Total: {len(proxies)}")


if __name__ == "__main__":
    main()
