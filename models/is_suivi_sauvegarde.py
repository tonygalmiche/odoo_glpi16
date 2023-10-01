# -*- coding: utf-8 -*-
from odoo import models,fields,api


class is_suivi_sauvegarde(models.Model):
    _name = "is.suivi.sauvegarde"
    _description = "Suivi des sauvegardes"
    _order='date desc, ordinateur_id'

    date            = fields.Date('Date de vérification de la sauvegarde', required=True, default=lambda *a: fields.datetime.now())
    ordinateur_id   = fields.Many2one('is.ordinateur', 'Serveur', required=True)
    site_id         = fields.Many2one('is.site', 'Site', related='ordinateur_id.site_id', readonly=True)
    resultat        = fields.Char('Résultat', required=True)
    logs            = fields.Text('Analyse des logs')


    def name_get(self, cr, uid, ids, context=None):
        res = []
        for obj in self.browse(cr, uid, ids, context=context):
            name=str(obj.date)+" "+obj.ordinateur_id.name
            res.append((obj.id,name))
        return res


    def acceder_suivi_sauvegarde(self):
        for obj in self:
            return {
                'name': u'Suivi sauvegarde '+obj.ordinateur_id.name or '',
                'view_mode': 'form,tree',
                'res_model': 'is.suivi.sauvegarde',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }

