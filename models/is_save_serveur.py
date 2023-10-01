# -*- coding: utf-8 -*-
from odoo import models,fields,api


class is_save_serveur(models.Model):
    _name = "is.save.serveur"
    _description = "Sauvegarde Serveur"
    _order='heure_debut desc'

    date            = fields.Date('Date sauvegarde'             , required=True)
    site_id         = fields.Many2one('is.site', 'Site')
    ordinateur_id   = fields.Many2one('is.ordinateur', 'Serveur', required=True)
    heure_debut     = fields.Datetime('Heure début')
    heure_fin       = fields.Datetime('Heure fin')
    temps           = fields.Integer('Temps (s)')
    nb_anomalies    = fields.Integer('Nb anomalies')
    resultat        = fields.Text('Résultat')


    # def name_get(self, cr, uid, ids, context=None):
    #     res = []
    #     for obj in self.browse(cr, uid, ids, context=context):
    #         name=str(obj.date)+" "+obj.ordinateur_id.name
    #         res.append((obj.id,name))
    #     return res




