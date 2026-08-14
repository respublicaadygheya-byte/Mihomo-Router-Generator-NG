import copy
from pathlib import Path
from typing import Any, Dict, List
import yaml


def load_warp_import(file_path: str | Path) -> List[Dict[str, Any]]:
    """Загружает внешние AmneziaWG / WARP профили из YAML методом 1:1 pass-through."""
    path = Path(file_path)

    if not path.exists():
        print(f"[WARP-IMPORT] Missing: {path}")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"[WARP-IMPORT] Error parsing YAML {path}: {e}")
        return []

    result = []

    for idx, proxy in enumerate(data.get("proxies", []), start=1):
        if not isinstance(proxy, dict):
            continue

        if proxy.get("type") != "wireguard":
            continue

        node = copy.deepcopy(proxy)

        # Сохраняем имя с префиксом WARP-AWG-{idx}
        node["name"] = f"WARP-AWG-{idx} {node.get('name', 'UNKNOWN')}"

        node.setdefault("udp", True)

        result.append(node)

    print(f"[WARP-IMPORT] Loaded {len(result)} nodes")
    return result
