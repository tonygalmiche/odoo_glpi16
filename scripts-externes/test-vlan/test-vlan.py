#!/usr/bin/env python3
import asyncio
import json
import socket
import unicodedata
import urllib.request
import dns.name
import dns.resolver
from dns.resolver import NXDOMAIN
from time import time
import importlib

# Chemin vers le fichier JSON de configuration des services.
# Si le fichier existe et est valide, il est utilisé en priorité.
# Laisser vide ('') pour toujours utiliser test-vlan-config.py.
# JSON_FILES = [
#     #'http://pg-raspberry-theia4/odoo-glpi/ports_ordinateurs.json',
#     '/tmp/ports_ordinateurs.json',
# ]


#JSON_FILE = 'http://pg-raspberry-theia4/odoo-glpi/ports_ordinateurs.json'
JSON_FILE = '/tmp/ports_ordinateurs.json'







def _load_services_from_json(path):
    """Charge SERVICES depuis un fichier JSON.

    Format attendu :
        [{"nom_poste": "vm-ldap", "ports": [{"nom": "ssh", "type": "tcp", "numero": 22}]}]

    Retourne une liste de tuples (host, port, proto) ou None si le fichier
    est absent, vide ou mal formé.
    """
    try:
        if path.startswith('http://') or path.startswith('https://'):
            with urllib.request.urlopen(path, timeout=10) as resp:
                data = json.load(resp)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        if not isinstance(data, list) or not data:
            return None
        services = []
        for entry in data:
            host = entry.get('nom_poste', '').strip().lower()
            ports = entry.get('ports', [])
            if not host or not isinstance(ports, list):
                continue
            for p in ports:
                if isinstance(p, dict):
                    port_num = p.get('numero')
                    proto = str(p.get('type', 'tcp')).strip().lower()
                    if port_num is not None:
                        services.append((host, str(port_num), proto))
        return services if services else None
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        return None


# Priorité au fichier JSON ; fallback sur test-vlan-config.py
_json_services = _load_services_from_json(JSON_FILE)
if _json_services is not None:
    SERVICES = _json_services
else:
    _cfg = importlib.import_module("test-vlan-config")
    SERVICES = _cfg.SERVICES


TIMEOUT = 5
DNS_SUFFIX = '.gray.plastigray.com'


def name_to_ip(hostname):
    n = dns.name.from_text(hostname + DNS_SUFFIX)
    answer = dns.resolver.resolve(n, 'A')
    return next(iter(answer)).to_text()


async def check_tcp_port(address, port):
    # Tentative de connexion asynchrone
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(address, port),
        timeout=TIMEOUT
    )
    # Fermeture propre de la connexion
    writer.close()
    await writer.wait_closed()


class EchoClientProtocol:
    def __init__(self, on_con_lost, result):
        self.on_con_lost = on_con_lost
        self.result = result
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        self.transport.sendto("0".encode())

    def datagram_received(self, data, addr):
        self.transport.close()
        self.result.append('open')

    def error_received(self, exc):
        self.transport.close()
        self.result.append('close')

    def connection_lost(self, exc):
        try:
            self.on_con_lost.set_result(True)
        except:
            pass


async def check_udp_port(address, port):
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()

    result = []
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: EchoClientProtocol(on_con_lost, result),
        remote_addr=(address, port))

    try:
        await asyncio.wait_for(
            on_con_lost,
            timeout=TIMEOUT
        )
        if not result or result[0] != 'open':
            raise ConnectionRefusedError()
    finally:
        transport.close()

async def check_port(hostname, port, proto):
    try:
        address = name_to_ip(hostname)
    except NXDOMAIN:
        return hostname, None, port, proto, 'unknown'
    try:
        if proto == 'tcp':
            func = check_tcp_port
        else:
            func = check_udp_port
        await func(address, port)
        status = 'open'
    except (TimeoutError, asyncio.TimeoutError):
        if proto == 'udp':
            # en UDP un timeout peut signifier que le service écoute mais attend des données
            status = 'open'
        else:
            status = 'timeout'
    except (ConnectionRefusedError, OSError) as err:
        status = 'close'
    return hostname, address, port, proto, status


def _dw(s):
    """Largeur d'affichage d'une chaîne dans le terminal (gère les emoji larges)."""
    w = 0
    for c in s:
        cp = ord(c)
        if 0xFE00 <= cp <= 0xFE0F:  # sélecteurs de variation (largeur 0)
            continue
        eaw = unicodedata.east_asian_width(c)
        w += 2 if eaw in ('W', 'F') else 1
    return w


def _pad(s, width):
    return s + ' ' * (width - _dw(s))


def get_source_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return 'inconnu'


async def main():
    services = [check_port(hostname, port, proto) for hostname, port, proto in SERVICES]
    ret = await asyncio.gather(
            *services
    )

    # Adresse IP source
    src_ip = get_source_ip()
    print(f"IP source : {src_ip}")
    print()

    STATUS_ICONS = {
        'open':    '✅ open',
        'close':   '❌ close',
        'timeout': '⌛ timeout',
        'unknown': '❓ unknown',
    }

    # Calcul des largeurs de colonnes (en tenant compte des caractères larges)
    col_host  = max(_dw('Hôte'),   max(_dw(d[0]) for d in ret))
    col_ip    = max(_dw('IP'),     max(_dw(d[1]) if d[1] else _dw('N/A') for d in ret))
    col_port  = max(_dw('Port'),   max(_dw(d[2]) for d in ret))
    col_proto = max(_dw('Proto'),  max(_dw(d[3]) for d in ret))
    col_stat  = max(_dw('Statut'), max(_dw(v) for v in STATUS_ICONS.values()))

    sep  = f"+{'-'*(col_host+2)}+{'-'*(col_ip+2)}+{'-'*(col_port+2)}+{'-'*(col_proto+2)}+{'-'*(col_stat+2)}+"
    head = f"| {_pad('Hôte', col_host)} | {_pad('IP', col_ip)} | {_pad('Port', col_port)} | {_pad('Proto', col_proto)} | {_pad('Statut', col_stat)} |"

    print(sep)
    print(head)
    print(sep)
    for hostname, address, port, proto, status in ret:
        ip_str = address if address else 'N/A'
        icon = STATUS_ICONS.get(status, f'? {status}')
        print(f"| {_pad(hostname, col_host)} | {_pad(ip_str, col_ip)} | {_pad(port, col_port)} | {_pad(proto, col_proto)} | {_pad(icon, col_stat)} |")
    print(sep)


# Commande a faire :
# ss -ltanpu|grep LISTEN

#vm-grafana-bookworm
#vm-dynacase-hapy3
#vm-apt-cacher-ng-bullseye
#vm-odoo-bullseye


if __name__ ==  '__main__':
    ori_time = time()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
    print()
    print("Temps d'exécution :", time() - ori_time)
