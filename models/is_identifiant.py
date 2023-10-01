# -*- coding: utf-8 -*-
from odoo import models,fields,api

class is_identifiant(models.Model):
    _name = "is.identifiant"
    _description = "Identifiants"
    _order='name,ordinateur_id'

    name             = fields.Char('Login'       , required=True)
    mot_de_passe     = fields.Char('Mot de passe', required=True)
    site_id          = fields.Many2one('is.site', 'Site', required=True)
    service_id       = fields.Many2one('is.service', 'Service')
    utilisateur_id   = fields.Many2one('is.utilisateur', 'Utilisateur')
    ordinateur_id    = fields.Many2one('is.ordinateur', 'Ordinateur')
    admin_ordinateur = fields.Boolean("Compte admin ordinateur"           , default=False)
    cpt_utilisateur  = fields.Boolean("Compte utilisateur ordinateur"     , default=False)
    lam_gray         = fields.Boolean('LAM Gray'                          , default=False)
    lam_st_brice     = fields.Boolean('LAM ST-Brice'                      , default=False)
    lam_pk           = fields.Boolean('LAM PK'                            , default=False)
    bluemind         = fields.Boolean('Odoo Agenda'                       , default=False)
    mail             = fields.Boolean('Mail FC-NET'                       , default=False)
    tightvnc         = fields.Boolean('TightVNC'                          , default=False)
    odoo             = fields.Boolean('Odoo'                              , default=False)
    microsoft        = fields.Boolean('Microsoft'                         , default=False, help=u'Compte Microsoft, Skype ou Teams')

    commentaire      = fields.Text('Commentaire')
    active           = fields.Boolean('Actif', default=True)


    def envoyer_identifiant_bluemind_action(self):
        for obj in self:
            if obj.bluemind == True:
                subject=u'['+obj.utilisateur_id.name+u'] Identifiant Odoo Agenda'
                email_to   = obj.utilisateur_id.mail
                user       = self.env['res.users'].browse(self._uid)
                email_from = user.email
                nom        = user.name
                if email_to :
                    body_html=u"""
                        <p>Bonjour,</p>
                        <p>Nous avons créé votre compte dans l'agenda partagé Odoo de Plastigray.</p>
                        <p>L'adresse pour y accéder est : <b><a href="https://odoo-agenda.plastigray.com">https://odoo-agenda.plastigray.com</a></b></p>
                        <p>
                            Vos identifiants sont :<br>
                            - Identifiant : <b>"""+obj.name+u"""</b><br>
                            - Mot de passe : <b>"""+obj.mot_de_passe+u"""</b><br>
                        </p>
                        <p>Cordialement</p>
                        <p>"""+nom+u"""</p>
                    """
                    vals={
                        'email_from'    : email_from, 
                        'email_to'      : email_to, 
                        'email_cc'      : email_from,
                        'subject'       : subject,
                        'body_html'     : body_html,
                    }
                    email=self.env['mail.mail'].create(vals)
                    if email:
                        self.env['mail.mail'].send(email)

