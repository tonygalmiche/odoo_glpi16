# -*- coding: utf-8 -*-
from odoo import models,fields,api
from datetime import datetime


class is_action(models.Model):
    _name = "is.action"
    _description = "Actions"
    _order='date_creation desc, name'


    @api.depends('ordinateur_id','utilisateur_id')
    def _compute(self):
        for obj in self:
            if obj.utilisateur_id.service_id.id:
                obj.service_id=obj.utilisateur_id.service_id.id
            if obj.utilisateur_id.site_id.id:
                obj.site_id=obj.utilisateur_id.site_id.id
            else:
                if obj.ordinateur_id.site_id.id:
                    obj.site_id=obj.ordinateur_id.site_id.id


    action_globale_id = fields.Many2one('is.action.globale', 'Action globale')
    name              = fields.Char('Action', required=True)
    ordinateur_id     = fields.Many2one('is.ordinateur', 'Ordinateur')
    utilisateur_id    = fields.Many2one('is.utilisateur', 'Utilisateur')
    site_id           = fields.Many2one('is.site'   , 'Site'   , compute='_compute', readonly=True, store=True)
    service_id        = fields.Many2one('is.service', 'Service', compute='_compute', readonly=True, store=True)
    mail              = fields.Char('Mail', related='utilisateur_id.mail', readonly=True)
    date_creation     = fields.Date('Date création', required=True, default=lambda *a: fields.datetime.now())
    date_prevue       = fields.Date('Date prévue'  , required=True)
    tps_prevu         = fields.Float("Temps prévu (H)")
    date_realisee     = fields.Date('Date réalisée')
    tps_passe         = fields.Float("Temps passé (H)")
    commentaire       = fields.Text('Commentaire')


    def solder_action_action(self):
        for obj in self:
            if obj.action_globale_id.date_realisee:
                if obj.date_realisee==False:
                    obj.date_realisee=obj.action_globale_id.date_realisee


    def actualiser_service_action(self):
        for obj in self:
            if obj.service_id.id==False:
                if obj.utilisateur_id.id!=False:
                    service_id=obj.utilisateur_id.service_id.id
                else:
                    service_id=obj.ordinateur_id.service_id.id
                if service_id:
                    obj.service_id=service_id


    def acceder_action(self):
        for obj in self:
            return {
                'name': u'Action '+obj.name or '',
                'view_mode': 'form,tree',
                'res_model': 'is.action',
                'res_id': obj.id,
                'type': 'ir.actions.act_window',
            }


    # def create(self, vals):
    #     obj = super(is_action, self).create(vals)
    #     obj.action_globale_id._compute_avancement()
    #     return obj


    # def write(self, vals):
    #     res=super(is_action, self).write(vals)
    #     for obj in self:
    #         if obj.action_globale_id:
    #             obj.action_globale_id._compute_avancement()
    #     return res


    def ordinateur_id_on_change(self,ordinateur_id,utilisateur_id):
        res={}
        if ordinateur_id:
            res['value']={}
            ordinateur = self.env['is.ordinateur'].browse(ordinateur_id)
            utilisateur_id=ordinateur.utilisateur_id.id
            if utilisateur_id:
                res['value']['utilisateur_id']=utilisateur_id
        return res


    def utilisateur_id_on_change(self,ordinateur_id,utilisateur_id):
        res={}
        if utilisateur_id and ordinateur_id==False:
            res['value']={}
            ordinateurs = self.env['is.ordinateur'].search([('utilisateur_id','=',utilisateur_id)])
            for ordinateur in ordinateurs:
                res['value']['ordinateur_id']=ordinateur.id
        return res




