# -*- coding: utf-8 -*-
from odoo import models,fields

class res_company(models.Model):
    _inherit = 'res.company'

    is_glpi_host    = fields.Char('Host GLPI')
    is_glpi_user    = fields.Char('User GLPI')
    is_glpi_passwd  = fields.Char('Mot de passe GLPI')
    is_glpi_db      = fields.Char('Base GLPI')
    is_serveur_sftp = fields.Char('Serveur SFTP (pure-ftp)')



