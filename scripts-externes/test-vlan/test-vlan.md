# test-vlan — Déploiement et test des VLAN

## Vue d'ensemble

Ces scripts permettent de déployer et d'exécuter un test de connectivité réseau
sur des postes répartis sur différents VLAN.

### Fichiers

| Fichier | Rôle |
|---|---|
| `test-vlan-deploiement.py` | Orchestre le déploiement et l'exécution distante |
| `test-vlan.py` | Teste la connectivité réseau (TCP/UDP) depuis le poste distant |
| `test-vlan-config.py` | Paramètres de connexion Odoo et listes statiques de secours |

---

## Prérequis

Sur la machine locale (qui lance le déploiement) :
```bash
sudo apt install python3-dnspython openssh-client
```

Sur les postes distants (où `test-vlan.py` est exécuté) :
```bash
sudo apt install python3-dnspython
```

La clé SSH de l'utilisateur local doit être autorisée sur :
- le **serveur Odoo** (pour le SCP du fichier JSON)
- chaque **poste cible** (pour le SCP + SSH d'exécution)

---


## Fonctionnement de `test-vlan-deploiement.py`

1. **Export JSON depuis Odoo** : appelle `exporter_ports_json_scheduler` sur
   `is.ordinateur` via XML-RPC, qui génère `ports_ordinateurs.json` dans le
   dossier `is_dossier_destination` de `res.company`.

2. **Récupération du JSON** : SCP du fichier depuis
   `<ODOO_SSH_USER>@<serveur_odoo>:<dossier>/ports_ordinateurs.json`
   vers `/tmp/ports_ordinateurs.json` en local.

3. **Récupération des postes cibles** : recherche dans `is.ordinateur` tous les
   enregistrements dont le champ `test_vlan` est renseigné. Le login SSH utilisé
   est celui du champ `login` de l'utilisateur affecté à l'ordinateur
   (`utilisateur_id`), ou `root` si aucun utilisateur n'est affecté.

4. **Déploiement sur chaque poste** :
   - SCP de `test-vlan.py`
   - SCP de `test-vlan-config.py`
   - SCP de `ports_ordinateurs.json`
   - Exécution distante de `test-vlan.py` via SSH

---

## Utilisation

### Déploiement sur tous les postes
```bash
./test-vlan-deploiement.py
```

### Filtres disponibles

#### `--filtre` — Filtrer par nom de poste (contient, insensible à la casse)
```bash
./test-vlan-deploiement.py --filtre pc-compta
./test-vlan-deploiement.py --filtre gray
```

#### `--filtre-vlan` — Filtrer par nom de VLAN (contient, insensible à la casse)
```bash
./test-vlan-deploiement.py --filtre-vlan vlan5
./test-vlan-deploiement.py --filtre-vlan "vlan10 gray"
```

#### Combinaison des deux filtres
```bash
./test-vlan-deploiement.py --filtre pc --filtre-vlan vlan5
```

#### `--filtre-port` — Tester uniquement certains ports (contient, insensible à la casse)

La valeur est une liste séparée par des virgules. Le filtre s'applique sur le **nom du port** ou le **nom du service** tel qu'il est dans le JSON.

```bash
./test-vlan-deploiement.py --filtre-port ssh
./test-vlan-deploiement.py --filtre-port ssh,https
./test-vlan-deploiement.py --filtre-port 22,443
```

#### Combinaison de tous les filtres
```bash
./test-vlan-deploiement.py --filtre pc --filtre-vlan vlan5 --filtre-port ssh,https
```

#### `--filtre-statut` — Afficher uniquement certains statuts (open, close, timeout, unknown)
```bash
./test-vlan-deploiement.py --filtre-statut timeout
./test-vlan-deploiement.py --filtre-statut timeout,close
```

#### Combinaison de tous les filtres
```bash
./test-vlan-deploiement.py --filtre-vlan pk --filtre-port ssh,https --filtre-statut timeout,close
```

---

## Odoo — Paramétrage

### `is.ordinateur`

| Champ | Utilisation |
|---|---|
| `name` | Nom du poste (= nom d'hôte réseau) |
| `test_vlan` | VLAN du poste (ex : `vlan5 Gray`). Si renseigné, le poste est inclus dans le déploiement. |
| `utilisateur_id` | Utilisateur affecté. Son `login` est utilisé pour la connexion SSH. |
| `port_ids` | Ports à tester (exportés dans le JSON). |

### `res.company`

| Champ | Utilisation |
|---|---|
| `is_dossier_destination` | Chemin absolu sur le serveur Odoo où est déposé `ports_ordinateurs.json`. |
