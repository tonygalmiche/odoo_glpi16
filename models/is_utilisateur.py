# -*- coding: utf-8 -*-
from odoo import models,fields,api
import base64


class is_service(models.Model):
    _name = "is.service"
    _description = "Service"
    _order='name'
    _sql_constraints = [('name_uniq','UNIQUE(name)', 'Ce code existe déjà')] 

    name            = fields.Char('Service', required=True)
    commentaire     = fields.Text('Commentaire')


class is_utilisateur(models.Model):
    _name = "is.utilisateur"
    _description = "Utilisateurs"
    _order='site_id,name'
    _sql_constraints = [
        ('name_uniq','UNIQUE(name)'  , 'Ce nom existe déjà'),
        ('login_uniq','UNIQUE(login)', 'Ce login existe déjà'),
    ] 

    site_id         = fields.Many2one('is.site', 'Site', required=True)
    name            = fields.Char('Prénom Nom', required=True)
    login           = fields.Char('Login'     , required=True)
    mail            = fields.Char('Mail')
    service_id      = fields.Many2one('is.service', 'Service')
    fonction        = fields.Char('Fonction')
    telephone       = fields.Char('Téléphone')
    portable        = fields.Char('Portable')
    fax             = fields.Char('Fax')
    autre           = fields.Char('Autre')
    commentaire     = fields.Text('Commentaire')
    action_ids      = fields.One2many('is.action', 'utilisateur_id', u'Actions', readonly=True)
    signature_mail  = fields.Html(u'Signature mail',sanitize=False)
    active          = fields.Boolean('Actif', default=True)


    def get_tr(self,val):
        if val and val!='':
            # val="""
            #     <tr>
            #         <td>
            #             <font size="2" color="#939393">%s</font>
            #         </td>
            #     </tr>
            # """%val
            val="""<font size="2" color="#939393">toto %s</font>"""%val
        else:
            val=''
        return val


    def generer_signature_mail(self):
        for obj in self:
            if not obj.site_id.signature_mail:
                raise Warning(u"Signature mail non renseignée pour le site "+obj.site_id.name)
            html=obj.site_id.signature_mail
            telephone = obj.telephone or ''
            portable  = obj.portable or ''
            fax       = obj.fax or ''
            if telephone != '':
                telephone = u'Tél : '+telephone
            if portable != '':
                portable = u'Mobile : '+portable
            if fax != '':
                fax = u'Fax : '+fax

            # fonction  = self.get_tr(obj.fonction)
            # telephone = self.get_tr(telephone)
            # portable  = self.get_tr(portable)
            # fax       = self.get_tr(fax)
            # autre     = self.get_tr(obj.autre)



            html = html.replace('${name}'     , (obj.name or ''))
            html = html.replace('${mail}'    , (obj.mail or ''))

            html = html.replace('${fonction}' , (obj.fonction or ''))
            html = html.replace('${telephone}', (obj.telephone or ''))
            html = html.replace('${portable}' , (obj.portable or ''))
            html = html.replace('${fax}'      , (obj.fax or ''))
            html = html.replace('${autre}'    , (obj.autre or ''))


            # html = html.replace('${fonction}' , (fonction or ''))



            # html = html.replace('<tr><td>${fonction}</td></tr>' , fonction)
            # html = html.replace('<tr><td>${telephone}</td></tr>', telephone)
            # html = html.replace('<tr><td>${portable}</td></tr>' , portable)
            # html = html.replace('<tr><td>${fax}</td></tr>'      , fax)
            # html = html.replace('<tr><td>${autre}</td></tr>'    , autre)
            if html:
                obj.signature_mail = html
            obj.generer_piece_jointe()


    def generer_piece_jointe(self):
        model=self._name
        for obj in self:
            if not obj.signature_mail:
                raise Warning(u"Signature mail non générée pour "+obj.name)
            name = 'signature-mail.html'
            path = '/tmp/' + name
            f = open(path,'wb')
            f.write(obj.signature_mail.encode('utf-8'))
            f.close()
            datas = open(path,'rb').read()
            #datas = open(path,'rb').read().encode('base64')

            # ** Recherche si une pièce jointe est déja associèe ***************
            attachment_obj = self.env['ir.attachment']
            model=self._name
            #name='commandes.pdf'
            attachments = attachment_obj.search([('res_model','=',model),('res_id','=',obj.id),('name','=',name)])
            # ******************************************************************

            # ** Creation ou modification de la pièce jointe *******************
            vals = {
                'name':        name,
                'type':        'binary',
                'res_model':   model,
                'res_id':      obj.id,
                'datas':       base64.b64encode(datas) #datas,
            }
            if attachments:
                for attachment in attachments:
                    attachment.write(vals)
            else:
                attachment = attachment_obj.create(vals)
            # ******************************************************************


    def envoyer_signature_mail(self):
        model=self._name
        for obj in self:
            self.generer_signature_mail()
            subject=u'['+obj.name+u'] Nouvelle signature de mail'
            email_to=obj.mail
            user  = self.env['res.users'].browse(self._uid)
            email_from = user.email
            email_to = obj.mail
            nom   = user.name
            # body_html=u"""
            #     <p>Bonjour,</p>
            #     <p>Voici la signature mail nouveau format, avec les liens vers les réseaux sociaux et le site de Plastigray.</p>
            #     <p>Vous trouverez ci-joint le fichier signature HTML à télécharger, ainsi que la procédure en PDF pour configurer le logiciel de messagerie.</p>
            #     <p>"""+nom+u"""</p>
            # """
            body_html = obj.site_id.contenu_mail
            attachment_ids = []
            attachment_obj = self.env['ir.attachment']
            attachments = attachment_obj.search([('res_model','=',model),('res_id','=',obj.id)])
            for attachment in attachments:
                attachment_ids.append(attachment.id)

            # ** Ajout des pieces jointes associèes au site ********************
            attachments = attachment_obj.search([('res_model','=','is.site'),('res_id','=',obj.site_id.id)])
            for attachment in attachments:
                attachment_ids.append(attachment.id)
            # ******************************************************************

            vals={
                'email_from'    : email_from, 
                'email_to'      : email_to, 
                'email_cc'      : email_from,
                'subject'       : subject,
                'body_html'     : body_html,
                'attachment_ids': [(6, 0, attachment_ids)] 
            }
            email=self.env['mail.mail'].create(vals)
            if email:
                self.env['mail.mail'].send(email)



class is_site(models.Model):
    _name = "is.site"
    _inherit=['mail.thread']
    _description = "Site"
    _order='name'

    name             = fields.Char(u'Site', required=True)
    code             = fields.Char(u'Code', required=True)
    signature_mail   = fields.Html(u'Modèle signature mail',sanitize=False)
    contenu_mail     = fields.Html(u'Contenu du mail',sanitize=False)
    dest_mozilla_ids = fields.Many2many('is.utilisateur', 'is_site_utilisateur_rel', 'ris_site_id','utilisateur_id', string="Destinataires des anomalies des sauvegardes de Mozilla")
