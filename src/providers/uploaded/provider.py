import os
import yaml
import glob
import json
import configparser

def parse_wg_conf(file_path):
    """Парсит обычный .conf / .ini файл WireGuard или Amnezia WireGuard в словарь прокси Mihomo"""
    config = configparser.ConfigParser()
    try:
        config.read(file_path, encoding='utf-8')
    except Exception as e:
        print(f"[UPLOADED] Error reading WG conf {file_path}: {e}")
        return None

    if not config.has_section('Interface') or not config.has_section('Peer'):
        return None

    interface = config['Interface']
    peer = config['Peer']

    # Извлекаем основные параметры WireGuard
    private_key = interface.get('PrivateKey', '').strip()
    address = interface.get('Address', '').strip()
    endpoint = peer.get('Endpoint', '').strip()
    public_key = peer.get('PublicKey', '').strip()
    
    if not private_key or not endpoint or not public_key:
        return None

    # Обрабатываем адрес (может быть списком через запятую)
    ip_address = address.split(',')[0].strip() if address else "10.2.0.2/32"
    
    # Разбиваем Endpoint на server и port
    if ":" in endpoint:
        if endpoint.startswith("["):
            server, port_str = endpoint.rsplit(":", 1)
            server = server.strip("[]")
        else:
            server, port_str = endpoint.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            port = 51820
    else:
        server = endpoint
        port = 51820

    file_name = os.path.basename(file_path)
    proxy_name = os.path.splitext(file_name)[0]

    proxy = {
        "name": proxy_name,
        "type": "wireguard",
        "server": server,
        "port": port,
        "ip": ip_address,
        "public-key": public_key,
        "private-key": private_key,
        "udp": True
    }

    # Поддержка специфических полей Amnezia WireGuard, если они есть в конфиге
    for key in ['magic', 'jc', 'jmin', 'jmax', 's1', 's2']:
        if key in interface:
            val = interface.get(key).strip()
            try:
                if '.' in val:
                    proxy[key] = float(val)
                else:
                    proxy[key] = int(val)
            except ValueError:
                proxy[key] = val

    return proxy

def get_proxies():
    uploaded_dir = "/root/Mihomo-Router-Generator-NG/UPLOADED"
    os.makedirs(uploaded_dir, exist_ok=True)
    
    all_proxies = []
    
    # 1. Ищем и обрабатываем YAML/YML файлы
    yaml_files = glob.glob(os.path.join(uploaded_dir, "*.yaml")) + glob.glob(os.path.join(uploaded_dir, "*.yml"))
    print(f"[UPLOADED PROVIDER] Scanning directory: {uploaded_dir}")
    print(f"[UPLOADED PROVIDER] Found YAML files: {len(yaml_files)}")
    
    for file_path in yaml_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not data:
                    continue
                if isinstance(data, dict) and "proxies" in data:
                    proxies = data["proxies"]
                    if isinstance(proxies, list):
                        all_proxies.extend(proxies)
                        print(f"[UPLOADED] Loaded {len(proxies)} proxies from {os.path.basename(file_path)}")
                elif isinstance(data, list):
                    all_proxies.extend(data)
                    print(f"[UPLOADED] Loaded {len(data)} proxies (list) from {os.path.basename(file_path)}")
                elif isinstance(data, dict) and "name" in data and "type" in data:
                    all_proxies.append(data)
                    print(f"[UPLOADED] Loaded 1 proxy from {os.path.basename(file_path)}")
        except Exception as e:
            print(f"[UPLOADED] Error reading {file_path}: {e}")

    # 2. Ищем и обрабатываем .conf файлы WireGuard / AWG
    conf_files = glob.glob(os.path.join(uploaded_dir, "*.conf"))
    print(f"[UPLOADED PROVIDER] Found WG/AWG .conf files: {len(conf_files)}")
    
    for file_path in conf_files:
        proxy = parse_wg_conf(file_path)
        if proxy:
            all_proxies.append(proxy)
            print(f"[UPLOADED] Loaded WG/AWG proxy from {os.path.basename(file_path)}")
            
    print(f"[UPLOADED PROVIDER] Total successfully loaded custom proxies: {len(all_proxies)}")
    return all_proxies

if __name__ == "__main__":
    proxies = get_proxies()
    cache_dir = "/root/Mihomo-Router-Generator-NG/cache/providers"
    os.makedirs(cache_dir, exist_ok=True)
    output_file = os.path.join(cache_dir, "uploaded-custom.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(proxies, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_file}")
