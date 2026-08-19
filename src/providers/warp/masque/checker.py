import tempfile
import subprocess
import os
import time
import requests
import yaml

def check_masque(node_config):
    import random
    mixed_port = random.randint(20000, 45000)
    
    proxy_item = {
        "name": "warp-test",
        "type": "wireguard",
        "magic": node_config.get("magic", ""),
        "jc": node_config.get("jc", 4),
        "jmin": node_config.get("jmin", 50),
        "jmax": node_config.get("jmax", 100),
        "s1": node_config.get("s1", 50),
        "s2": node_config.get("s2", 70),
        "server": node_config["server"],
        "port": node_config["port"],
        "ip": node_config["ip"],
        "ipv6": node_config.get("ipv6", ""),
        "private-key": node_config["private-key"],
        "public-key": node_config["public-key"],
        "reserved": node_config.get("reserved", [0, 0, 0])[:3],
        "udp": True,
        "mtu": 1280,
        "remote-dns-resolve": True
    }

    config_data = {
        "mixed-port": mixed_port,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "warning",  # Поставим warning, чтобы видеть, если ядро ругается на конфиг
        "proxies": [proxy_item]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tf:
        yaml.dump(config_data, tf)
        temp_filename = tf.name

    mihomo_bin = "./bin/mihomo"
    if not os.path.exists(mihomo_bin):
        import shutil
        mihomo_bin = shutil.which("mihomo") or "mihomo"

    process = None
    try:
        process = subprocess.Popen(
            [mihomo_bin, "-d", os.path.dirname(temp_filename), "-f", temp_filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Дадим ядру 1.5 секунды на старт
        time.sleep(1.5)

        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"[WARP CHECK] Mihomo failed for {node_config['server']}:{node_config['port']}. Output: {stderr.strip() or stdout.strip()}")
            return None

        proxies = {
            "http": f"http://127.0.0.1:{mixed_port}",
            "https": f"http://127.0.0.1:{mixed_port}"
        }
        
        start_time = time.time()
        response = requests.get("http://www.gstatic.com/generate_204", proxies=proxies, timeout=4)
        latency = int((time.time() - start_time) * 1000)

        if response.status_code == 204:
            node_config["latency"] = latency
            return node_config

    except Exception:
        pass
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1)
            except:
                process.kill()
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    return None
