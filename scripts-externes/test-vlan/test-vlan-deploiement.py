#!/usr/bin/env python3
"""
Déploie test-vlan.py et test-vlan-config.py sur chaque poste listé dans VLANS
de test-vlan-config.py, copie aussi /tmp/ports_ordinateurs.json, puis exécute
test-vlan.py à distance via SSH.

La liste des postes est récupérée depuis Odoo (is.ordinateur) via XML-RPC :
tout ordinateur dont le champ test_vlan est renseigné est inclus.
"""
import argparse
import importlib
import os
import ssl
import subprocess
import sys
import urllib.parse
import xmlrpc.client

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VLAN_SCRIPT   = os.path.join(SCRIPT_DIR, 'test-vlan.py')
VLAN_CONFIG   = os.path.join(SCRIPT_DIR, 'test-vlan-config.py')
PORTS_JSON    = '/tmp/ports_ordinateurs.json'
REMOTE_DIR    = '/tmp'

# Contexte SSL sans vérification du certificat
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def odoo_connect(url, db, user, password):
    """Authentifie sur Odoo et retourne (uid, models_proxy)."""
    transport = xmlrpc.client.SafeTransport(context=_SSL_CTX)
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', transport=transport)
    uid = common.authenticate(db, user, password, {})
    if not uid:
        print("[ERREUR] Authentification Odoo échouée.", file=sys.stderr)
        sys.exit(1)
    models_proxy = xmlrpc.client.ServerProxy(
        f'{url}/xmlrpc/2/object',
        transport=xmlrpc.client.SafeTransport(context=_SSL_CTX),
        allow_none=True,
    )
    return uid, models_proxy


def exporter_et_recuperer_ports_json(url, db, user, password, ssh_user, debug=False):
    """Déclenche l'export ports JSON sur le serveur Odoo, récupère le fichier
    via SCP et le dépose dans PORTS_JSON."""
    uid, models_proxy = odoo_connect(url, db, user, password)

    # 1. Déclencher l'export sur le serveur Odoo
    if debug:
        print("Déclenchement de exporter_ports_json_scheduler sur Odoo...")
    models_proxy.execute_kw(db, uid, password, 'is.ordinateur', 'exporter_ports_json_scheduler', [[]])

    # 2. Récupérer le dossier de destination depuis res.company
    companies = models_proxy.execute_kw(
        db, uid, password,
        'res.company', 'search_read',
        [[]],
        {'fields': ['is_dossier_destination'], 'limit': 1},
    )
    dossier = companies[0].get('is_dossier_destination') if companies else None
    if not dossier:
        print("[ERREUR] is_dossier_destination non configuré dans res.company.", file=sys.stderr)
        sys.exit(1)

    # 3. SCP depuis le serveur Odoo vers local
    hostname = urllib.parse.urlparse(url).hostname
    remote_src = f"{ssh_user}@{hostname}:{dossier}/ports_ordinateurs.json"
    if debug:
        print(f"  SCP  {remote_src}  →  {PORTS_JSON}")
    result = subprocess.run(['scp', '-q', '-o', 'StrictHostKeyChecking=no', remote_src, PORTS_JSON])
    if result.returncode != 0:
        print(f"  [ERREUR] Impossible de récupérer ports_ordinateurs.json depuis {hostname}", file=sys.stderr)
        sys.exit(1)
    if debug:
        print(f"  ports_ordinateurs.json récupéré dans {PORTS_JSON}")


def get_vlans_from_odoo(url, db, user, password, filtre=None, filtre_vlan=None):
    """Récupère depuis Odoo la liste (test_vlan, 'login@name') pour tous les
    is.ordinateur dont le champ test_vlan est renseigné.
    Si filtre est fourni, seuls les postes dont le nom contient cette chaîne sont retenus.
    Si filtre_vlan est fourni, seuls les postes dont le VLAN contient cette chaîne sont retenus."""
    uid, models = odoo_connect(url, db, user, password)
    domain = [['test_vlan', '!=', False]]
    if filtre:
        domain.append(['name', 'ilike', filtre])
    if filtre_vlan:
        domain.append(['test_vlan', 'ilike', filtre_vlan])
    records = models.execute_kw(
        db, uid, password,
        'is.ordinateur', 'search_read',
        [domain],
        {'fields': ['name', 'test_vlan', 'utilisateur_id'], 'order': 'name'},
    )

    vlans = []
    for r in records:
        nom_poste = r['name']
        vlan_name = r['test_vlan']
        utilisateur = r.get('utilisateur_id')
        if utilisateur:
            # Récupérer le login de l'utilisateur
            utilisateur_id = utilisateur[0]
            u = models.execute_kw(
                db, uid, password,
                'is.utilisateur', 'read',
                [[utilisateur_id]],
                {'fields': ['login']},
            )
            login = u[0]['login'] if u else 'root'
        else:
            login = 'root'
        vlans.append((vlan_name, f"{login}@{nom_poste}"))
    return vlans


def scp(local_path, remote_target, debug=False):
    """Copie un fichier local vers remote_target (user@host:/chemin)."""
    cmd = ['scp', '-q', local_path, remote_target]
    if debug:
        print(f"  SCP  {local_path}  →  {remote_target}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  [ERREUR] scp a échoué (code {result.returncode})", file=sys.stderr)
    return result.returncode == 0


def ssh_run(user_host, remote_cmd, debug=False):
    """Exécute une commande sur le poste distant via SSH."""
    cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', user_host, remote_cmd]
    if debug:
        print(f"  SSH  {user_host}  »  {remote_cmd}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  [ERREUR] ssh a échoué (code {result.returncode})", file=sys.stderr)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description='Déploie test-vlan.py sur les postes Odoo.')
    parser.add_argument('--filtre', metavar='TEXTE', default=None,
                        help='Filtrer les postes dont le nom contient TEXTE (insensible à la casse)')
    parser.add_argument('--filtre-vlan', metavar='VLAN', default=None,
                        help='Filtrer les postes dont le VLAN contient VLAN (insensible à la casse)')
    parser.add_argument('--filtre-port', metavar='PORT,...', default=None,
                        help='Tester uniquement les ports dont le nom contient un des termes (ex: ssh,https)')
    parser.add_argument('--filtre-statut', metavar='STATUT,...', default=None,
                        help='Afficher uniquement les lignes avec ce statut (ex: timeout,close)')
    parser.add_argument('--debug', action='store_true',
                        help='Afficher les commandes SCP et SSH exécutées')
    args = parser.parse_args()

    # Import dynamique de test-vlan-config pour récupérer les paramètres Odoo
    sys.path.insert(0, SCRIPT_DIR)
    cfg = importlib.import_module('test-vlan-config')

    odoo_url      = getattr(cfg, 'ODOO_URL', None)
    odoo_db       = getattr(cfg, 'ODOO_DB', None)
    odoo_user     = getattr(cfg, 'ODOO_USER', None)
    odoo_password = getattr(cfg, 'ODOO_PASSWORD', None)
    odoo_ssh_user = getattr(cfg, 'ODOO_SSH_USER', 'odoo')

    if not all([odoo_url, odoo_db, odoo_user, odoo_password]):
        print("[ERREUR] Paramètres Odoo non configurés dans test-vlan-config.py.", file=sys.stderr)
        sys.exit(1)

    # Export et récupération du fichier ports JSON depuis le serveur Odoo
    exporter_et_recuperer_ports_json(odoo_url, odoo_db, odoo_user, odoo_password, odoo_ssh_user, debug=args.debug)

    filtre_msg = ''
    if args.filtre:
        filtre_msg += f" (filtre poste : '{args.filtre}')"
    if args.filtre_vlan:
        filtre_msg += f" (filtre VLAN : '{args.filtre_vlan}')"
    print(f"Récupération des postes depuis Odoo (is.ordinateur, test_vlan renseigné){filtre_msg}...")
    vlans = get_vlans_from_odoo(odoo_url, odoo_db, odoo_user, odoo_password, filtre=args.filtre, filtre_vlan=args.filtre_vlan)
    if not vlans:
        print("Aucun poste avec test_vlan renseigné dans Odoo.")
        sys.exit(0)
    print(f"{len(vlans)} poste(s) trouvé(s) dans Odoo.")

    for idx, (vlan_name, user_host) in enumerate(vlans, 1):
        total = len(vlans)
        # 1. Copie de test-vlan.py
        scp(VLAN_SCRIPT, f"{user_host}:{REMOTE_DIR}/", debug=args.debug)

        # 2. Copie de test-vlan-config.py
        scp(VLAN_CONFIG, f"{user_host}:{REMOTE_DIR}/", debug=args.debug)

        # 3. Copie de ports_ordinateurs.json (si disponible)
        if os.path.exists(PORTS_JSON):
            scp(PORTS_JSON, f"{user_host}:{REMOTE_DIR}/", debug=args.debug)
        else:
            print(f"  [AVERTISSEMENT] {PORTS_JSON} introuvable, ignoré.")

        # 4. Exécution distante
        remote_cmd = f"python3 {REMOTE_DIR}/test-vlan.py --vlan {vlan_name!r} --host {user_host!r} --index {idx} --total {total}"
        if args.filtre_port:
            remote_cmd += f" --filtre-port {args.filtre_port}"
        if args.filtre_statut:
            remote_cmd += f" --filtre-statut {args.filtre_statut}"
        if args.debug:
            remote_cmd += " --debug"
        ssh_run(user_host, remote_cmd, debug=args.debug)


if __name__ == '__main__':
    main()
