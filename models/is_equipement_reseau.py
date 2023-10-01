# -*- coding: utf-8 -*-
from odoo import models,fields,api

class is_equipement_reseau(models.Model):
    _name = "is.equipement.reseau"
    _description = "Equipement reseau"
    _order='ordinateur_id'

    adresse_ip           = fields.Char('Adresse IP')
    adresse_mac          = fields.Char('Adresse MAC')
    site_id              = fields.Many2one('is.site', 'Site')
    ordinateur_id        = fields.Many2one('is.ordinateur', 'Ordinateur')
    date_creation        = fields.Datetime('Date de création')
    date_modification    = fields.Datetime('Date de modification')
    dhcp_end             = fields.Datetime('Date validité dhcp')
    dhcp_hostname        = fields.Char("Hostname dhcp")
    description_arp      = fields.Char("Description arp")
    origine_modification = fields.Char('Origine de la modification')
    commentaire          = fields.Text('Commentaire')
    adresse_principale   = fields.Boolean('Adresse réseau principale', default=True, help="Adresse utilisée pour la sauvegarde des messageries")
    active               = fields.Boolean('Actif', default=True)


    def name_get(self, cr, uid, ids, context=None):
        res = []
        for obj in self.browse(cr, uid, ids, context=context):
            name=str(obj.adresse_ip)
            res.append((obj.id,name))
        return res




