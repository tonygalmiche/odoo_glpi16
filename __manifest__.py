# -*- coding: utf-8 -*-
{
    "name" : "InfoSaône - Module Odoo 16 pour GLPI",
    "version" : "0.2",
    "author" : "InfoSaône",
    "category" : "InfoSaône",
    "description": """
InfoSaône - Module Odoo 16 pour GLPI
    """,
    "maintainer": 'InfoSaône',
    "website": 'http://www.infosaone.com',
    "depends" : [
        "base",
        "mail",
        #"document",
    ], 
    "data" : [
        "security/ir.model.access.csv",
        "views/is_utilisateur_view.xml",
        "views/is_ordinateur_view.xml",
        "views/is_logiciel_view.xml",
        "views/is_action_view.xml",
        "views/is_action_globale_view.xml",
        "views/is_identifiant_view.xml",
        "views/is_save_mozilla_view.xml",
        "views/is_save_serveur_view.xml",
        "views/is_suivi_sauvegarde_view.xml",
        "views/is_equipement_reseau_view.xml",
        "views/is_pureftp_view.xml",
        "views/res_company_view.xml",
        # "views/assets.xml",
        "views/menu.xml",
    ], 
    "installable": True,
    "active": False,
    "application": True,
    "license": "LGPL-3",
}

