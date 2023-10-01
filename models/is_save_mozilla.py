# -*- coding: utf-8 -*-
from odoo import models,fields,api
from datetime import datetime, date
import logging
_logger = logging.getLogger(__name__)

class is_save_mozilla(models.Model):
    _name = "is.save.mozilla"
    _description = "Sauvegarde Mozilla"
    _order='heure_debut desc'

    date            = fields.Date('Date sauvegarde')
    site_id         = fields.Many2one('is.site', 'Site')
    service_id      = fields.Many2one('is.service', 'Service')
    utilisateur_id  = fields.Many2one('is.utilisateur', 'Utilisateur')
    ordinateur_id   = fields.Many2one('is.ordinateur', 'Ordinateur')
    partage         = fields.Char('Partage')
    mail            = fields.Char('Mail')
    taille          = fields.Integer('Taille (Mo)')
    nb_modifs       = fields.Integer('Nb modifs')
    heure_debut     = fields.Datetime('Heure début')
    heure_fin       = fields.Datetime('Heure fin')
    temps           = fields.Integer('Temps (s)')
    resultat        = fields.Text('Résultat')


    def name_get(self, cr, uid, ids, context=None):
        res = []
        for obj in self.browse(cr, uid, ids, context=context):
            name=str(obj.heure_debut)+" "+obj.ordinateur_id.name
            res.append((obj.id,name))
        return res


    def mail_anomalie_sauvegarde_scheduler_action(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        self.mail_anomalie_sauvegarde_action(cr, uid, context)


    def mail_anomalie_sauvegarde_action(self):
        sites  = self.env['is.site'].search([])
        for site in sites:
            email_to=[]
            for dest in site.dest_mozilla_ids:
                email_to.append(dest.name+u' <'+dest.mail+u'>')
            if len(email_to)>0:
                self.mail_anomalie_sauvegarde_site(site,email_to)


    def mail_anomalie_sauvegarde_site(self,site,email_to):
        date=date.today()
        filtre=[
            ('utilisateur_id.site_id.id','=',site.id),
            ('date','=',date),
            ('partage','=','Thunderbird'),
        ]
        rows  = self.env['is.save.mozilla'].search(filtre, order='heure_debut')
        html=u"""
            <table style="">
                <thead>
                    <tr>
                        <th>Utilisateur</th>
                        <th>Ordinateur</th>
                        <th>Début</th>
                        <th>Fin</th>
                        <th>Durée (mn)</th>
                        <th>Taille (go)</th>
                        <th>Nb modifs</th>
                        <th>Résultat</th>
                    </tr>
                </thead>
                <tbody>
        """
        for row in rows:
            nb_modifs_color='white'
            if row.nb_modifs==0:
                nb_modifs_color='orange'
            temps_color='white'
            if row.temps>=900:
                temps_color='orange'
            resultat_color='white'
            if row.resultat=="OK" and row.nb_modifs>0:
                resultat_color='green'

            if row.nb_modifs==0 and row.resultat=="OK":
                row.resultat="Nb modifs = 0 ! (Le partage n'est probablement pas le bon)"
            html+=u"""
                <tr>
                    <td style="text-align:left">"""+row.utilisateur_id.name+"""</td>
                    <td style="text-align:left">"""+row.ordinateur_id.name+"""</td>
                    <td style="text-align:center">"""+utc2local(row.heure_debut)+"""</td>
                    <td style="text-align:center">"""+utc2local(row.heure_fin)+"""</td>
                    <td style="text-align:right;background-color:"""+temps_color+"""">"""+"{:10.1f}".format(row.temps/60.0)+"""</td>
                    <td style="text-align:right">"""+"{:10.2f}".format(row.taille/1024.0)+"""</td>
                    <td style="text-align:right;background-color:"""+nb_modifs_color+"""">"""+str(row.nb_modifs)+"""</td>
                    <td style="text-align:left;width:50%;background-color:"""+resultat_color+"""">"""+row.resultat+"""</td>
                </tr>
            """
        html+="</tbody></table>"
        user  = self.env['res.users'].browse(self._uid)
        subject=u"Anomalies sauvegarde Thunderbird "+site.name+" du "+str(date)
        body_html=u"""
            <html>
                <head>
                    <meta content="text/html; charset=UTF-8" http-equiv="Content-Type">
                    <style>
                        table {
                            border:1px solid black;
                            width:100%;
                            border-collapse:collapse;
                        }
                        td,th { 
                            border:1px solid black;
                            padding:0.5em;
                            margin:0.5em;
                        }
                    </style>
                </head>
                <body>
                    <h2>"""+subject+"""</h2>
                    """+html+"""
                </body>
            </html>
        """
        email_vals={
            'subject'       : subject,
            'email_to'      : ';'.join(email_to), 
            'email_cc'      : "",
            'email_from'    : "robot@plastigray.com", 
            'body_html'     : body_html.encode('utf-8'), 
        }
        email_id=self.env['mail.mail'].create(email_vals)
        self.env['mail.mail'].send(email_id)
        _logger.info(subject)


    def mail_anomalie_tps_sauvegarde_scheduler_action(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        self.mail_anomalie_tps_sauvegarde_action(cr, uid, context)


    def mail_anomalie_tps_sauvegarde_action(self):
        date=date.today()
        filtre=[
            ('date','=',date.today()),
            ('utilisateur_id.site_id.name','=','Gray'),
            ('partage','=','Thunderbird'),
            ('resultat','=','OK'),
            ('nb_modifs','>',0),
            ('temps','>',900),
        ]
        rows  = self.env['is.save.mozilla'].search(filtre, order='temps desc')
        html=u"""
            <table>
                <thead>
                    <tr>
                        <th>Utilisateur</th>
                        <th>Début</th>
                        <th>Fin</th>
                        <th>Durée (mn)</th>
                        <th>Taille (go)</th>
                    </tr>
                </thead>
                <tbody>
        """
        email_to=[]
        for row in rows:
            email_to.append(row.utilisateur_id.name+u' <'+row.utilisateur_id.mail+u'>')
            html+=u"""
                <tr>
                    <td style="text-align:left"  >"""+row.utilisateur_id.name+"""</td>
                    <td style="text-align:center">"""+utc2local(row.heure_debut)+"""</td>
                    <td style="text-align:center">"""+utc2local(row.heure_fin)+"""</td>
                    <td style="text-align:right;">"""+"{:10.1f}".format(row.temps/60.0)+"""</td>
                    <td style="text-align:right" >"""+"{:10.2f}".format(row.taille/1024.0)+"""</td>
                </tr>
            """
        html+="</tbody></table>"
        user  = self.env['res.users'].browse(self._uid)
        email_cc=[]
        email_cc.append(user.name+u' <'+user.email+u'>')
        subject=u"Temps de sauvegarde de Thunderbird >15mn du "+str(date)
        body_html=u"""
            <html>
                <head>
                    <meta content="text/html; charset=UTF-8" http-equiv="Content-Type">
                    <style>
                        table {

                            border:1px solid black;
                            width:1024px;
                            border-collapse:collapse;
                        }

                        td,th { 
                            border:1px solid black;
                            padding:0.5em;
                            margin:0.5em;
                        }
                    </style>
                </head>
                <body>
                    <p>Bonjour,</p>
                    <p>Le temps de sauvegarde de votre messagerie est supérieure à 15mn.</p>
                    <p>Pour que les messageries de tout le monde soient sauvegardées pendant la journée, il est important de ne pas dépasser 15mn.</p>
                    <p>Pour cela, il faut réduire la taille de votre messagerie et/ou mieux organiser son arborescence.</p>
                    <p>Merci de voir avec le service informatique pour plus d'informations ou pour vous aider à réduire ce temps.</p>
                    <br>
                    """+html+"""
                </body>
            </html>
        """
        email_vals={
            'subject'       : subject,
            'email_to'      : ';'.join(email_to), 
            'email_cc'      : ';'.join(email_cc),
            'email_from'    : "robot@plastigray.com", 
            'body_html'     : body_html.encode('utf-8'), 
        }
        email_id=self.env['mail.mail'].create(email_vals)
        self.env['mail.mail'].send(email_id)
        _logger.info(subject)




# def utc2local(date):
#     # Timezone en UTC
#     utc = pytz.utc
#     # DateTime à partir d'une string avec ajout de la timezone
#     utc_dt  = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=utc)
#     # Timezone Europe/Paris
#     europe = pytz.timezone('Europe/Paris')
#     # Convertion de la datetime utc en datetime localisée
#     loc_dt = utc_dt.astimezone(europe)
#     # Retour de la datetime localisée en string
#     #return loc_dt.strftime('%d/%m/%Y %H:%M')
#     return loc_dt.strftime('%H:%M')





