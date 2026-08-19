import ipaddress
import random

def scan_endpoints(account):
    print("[WARP SCANNER] Generating extended endpoint candidates...")
    
    base_cidrs = [
        "162.159.192.0/24",
        "162.159.193.0/24",
        "162.159.195.0/24",
        "188.114.96.0/24",
        "188.114.97.0/24",
        "188.114.98.0/24",
        "188.114.99.0/24"
    ]
    
    ports = [443, 2408, 500, 1701, 4500, 8443, 4443]
    candidates = []
    
    for cidr in base_cidrs:
        net = ipaddress.ip_network(cidr)
        hosts = list(net.hosts())
        selected_hosts = random.sample(hosts, min(20, len(hosts)))
        for ip in selected_hosts:
            port = random.choice(ports)
            candidates.append({
                "server": str(ip),
                "port": port
            })
            
    fallback_domains = [
        "engage.cloudflareclient.com",
        "cloudflareaccess.com"
    ]
    for domain in fallback_domains:
        candidates.append({"server": domain, "port": 2408})
        candidates.append({"server": domain, "port": 443})

    print(f"[WARP SCANNER] Total generated candidates: {len(candidates)}")
    return candidates
