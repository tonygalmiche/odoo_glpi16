#!/usr/bin/env python3
"""
Déploie test-vlan.py et test-vlan-config.py sur chaque poste listé dans VLANS
de test-vlan-config.py, copie aussi /tmp/ports_ordinateurs.json, puis exécute
test-vlan.py à distance via SSH.
"""
import importlib
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VLAN_SCRIPT   = os.path.join(SCRIPT_DIR, 'test-vlan.py')
VLAN_CONFIG   = os.path.join(SCRIPT_DIR, 'test-vlan-config.py')
PORTS_JSON    = '/tmp/ports_ordinateurs.json'
REMOTE_DIR    = '/tmp'


def scp(local_path, remote_target):
    """Copie un fichier local vers remote_target (user@host:/chemin)."""
    cmd = ['scp', '-q', local_path, remote_target]
    print(f"  SCP  {local_path}  →  {remote_target}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  [ERREUR] scp a échoué (code {result.returncode})", file=sys.stderr)
    return result.returncode == 0


def ssh_run(user_host, remote_cmd):
    """Exécute une commande sur le poste distant via SSH."""
    cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', user_host, remote_cmd]
    print(f"  SSH  {user_host}  »  {remote_cmd}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  [ERREUR] ssh a échoué (code {result.returncode})", file=sys.stderr)
    return result.returncode == 0


def main():
    # Import dynamique de test-vlan-config pour récupérer VLANS
    sys.path.insert(0, SCRIPT_DIR)
    cfg = importlib.import_module('test-vlan-config')
    vlans = getattr(cfg, 'VLANS', [])

    if not vlans:
        print("Aucun VLAN défini dans test-vlan-config.py (VLANS vide).")
        sys.exit(0)

    for vlan_name, user_host in vlans:
        print(f"\n{'='*60}")
        print(f"VLAN : {vlan_name}  ({user_host})")
        print(f"{'='*60}")

        # 1. Copie de test-vlan.py
        scp(VLAN_SCRIPT, f"{user_host}:{REMOTE_DIR}/")

        # 2. Copie de test-vlan-config.py
        scp(VLAN_CONFIG, f"{user_host}:{REMOTE_DIR}/")

        # 3. Copie de ports_ordinateurs.json (si disponible)
        if os.path.exists(PORTS_JSON):
            scp(PORTS_JSON, f"{user_host}:{REMOTE_DIR}/")
        else:
            print(f"  [AVERTISSEMENT] {PORTS_JSON} introuvable, ignoré.")

        # 4. Exécution distante
        ssh_run(user_host, f"python3 {REMOTE_DIR}/test-vlan.py")


if __name__ == '__main__':
    main()
