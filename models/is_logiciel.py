# -*- coding: utf-8 -*-
from odoo import models,fields,api

class is_logiciel(models.Model):
    _name = "is.logiciel"
    _description = "Logiciel"
    _order='logiciel,version'
    _sql_constraints = [('logiciel_version_uniq','UNIQUE(logiciel_id,version_id)', 'Ce logiciel existe deja !')] 

    logiciel     = fields.Char('Logiciel'      , index=1)
    logiciel_id  = fields.Integer('Logiciel id', index=1)
    version      = fields.Char('Version'       , index=1)
    version_id   = fields.Integer('Version id' , index=1)
    nb           = fields.Integer('Nb installations')
    ordinateurs  = fields.Text('Ordinateurs')
    commentaire  = fields.Text('Commentaire')
    state        = fields.Selection([
        ('ignore'  , u'Ignoré'),
        ('autorise', u'Autorisé'),
        ('interdit', u'Interdit'),
    ], "Etat")


    def etat_ignore_action(self):
        for obj in self:
            obj.state="ignore"


    def etat_autorise_action(self):
        for obj in self:
            obj.state="autorise"


    def etat_interdit_action(self):
        for obj in self:
            obj.state="interdit"
