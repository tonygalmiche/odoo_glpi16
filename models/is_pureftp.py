# -*- coding: utf-8 -*-
from odoo import models,fields,api           # type: ignore
from odoo.exceptions import ValidationError  # type: ignore
from random import randint

from subprocess import PIPE, Popen



import re
import os
import logging
_logger = logging.getLogger(__name__)



class is_pureftp(models.Model):
    _name = "is.pureftp"
    _description = "Pure-FTP"
    _order='name'

    _sql_constraints = [
        ('name_uniq'       , 'unique(name)'       , u"Ce compte existe déjà !"),
    ]

    name         = fields.Char('Login', required=True)
    mot_de_passe = fields.Char('Mot de passe')
    dossier      = fields.Char('Dossier', readonly=True)
    commentaire  = fields.Text('Commentaire')


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals['mot_de_passe']==False:
                regexp = r"(^[a-z0-9]{3,20})"
                if re.match(regexp, vals['name']) is None:
                    raise ValidationError(u"Le login ne doit contenir que des minuscules et faire entre 4 et 20 caractères !")
                X1=chr(randint(65,90));
                X2=chr(randint(65,90));
                X3=chr(randint(48,57));
                X4=chr(randint(48,57));
                X5=chr(randint(65,90));
                X6=chr(randint(65,90));
                X7=chr(randint(48,57));
                X8=chr(randint(48,57));
                mot_de_passe=X1+X2+X3+X4+X5+X6+X7+X8
                vals['mot_de_passe'] = mot_de_passe
            vals['dossier']  = '/PURE-FTP/'+vals['name']
        obj = super().create(vals_list)
        obj.update_pureftp()
        return obj


    # @api.model
    # def create(self, vals):
    #     if vals['mot_de_passe']==False:
    #         regexp = r"(^[a-z0-9]{3,20})"
    #         if re.match(regexp, vals['name']) is None:
    #             raise Warning(u"Le login ne doit contenir que des minuscules et faire entre 4 et 20 caractères !")
    #         X1=chr(randint(65,90));
    #         X2=chr(randint(65,90));
    #         X3=chr(randint(48,57));
    #         X4=chr(randint(48,57));
    #         X5=chr(randint(65,90));
    #         X6=chr(randint(65,90));
    #         X7=chr(randint(48,57));
    #         X8=chr(randint(48,57));
    #         mot_de_passe=X1+X2+X3+X4+X5+X6+X7+X8
    #         vals['mot_de_passe'] = mot_de_passe
    #     vals['dossier']  = '/PURE-FTP/'+vals['name']
    #     obj = super(is_pureftp, self).create(vals)
    #     obj.update_pureftp()
    #     return obj


    def write(self,vals):
        if 'name' in vals or 'mot_de_passe' in vals:
            raise Warning(u"Le login ou le mot de passe ne sont pas modifiable. Il faut supprimer et recréer le compte !")
        obj = super(is_pureftp, self).write(vals)
        return obj


    def unlink(self):
        company = self.env.user.company_id
        serveur_sftp = company.is_serveur_sftp
        if serveur_sftp:
            for obj in self:
                cmd="ssh root@%s pure-pw userdel %s "%(serveur_sftp,obj.name)
                _logger.info(cmd)
                lines=os.popen(cmd).readlines()
                for line in lines:
                    _logger.info(line.strip())
                cmd=u"ssh root@%s rm -Rf /PURE-FTP/%s"%(serveur_sftp,obj.name)
                _logger.info(cmd)
                lines=os.popen(cmd).readlines()
                for line in lines:
                    _logger.info(line.strip())
        res=super(is_pureftp, self).unlink()


    def update_pureftp(self):
        company = self.env.user.company_id
        serveur_sftp = company.is_serveur_sftp
        for obj in self:
            cmd="ssh -t root@%s /opt/pure-pw.sh %s %s"%(serveur_sftp,obj.name,obj.mot_de_passe)

            p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            _logger.info("%s => %s"%(cmd,stdout.decode()))
            if stderr:
                _logger.info("%s => %s"%(cmd,stderr.decode()))


            #_logger.info(cmd)
            ##lines=os.popen(cmd).readlines()
            #for line in lines:
            #    _logger.info(line.strip())










