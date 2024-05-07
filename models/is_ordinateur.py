# -*- coding: utf-8 -*-
from odoo import models,fields,api
import MySQLdb
import logging
_logger = logging.getLogger(__name__)


class is_partage(models.Model):
    _name = "is.partage"
    _description = "Partages Windows"
    _order='name'

    name = fields.Char('Partage', required=True)


class is_bureau(models.Model):
    _name = "is.bureau"
    _inherit=['mail.thread']
    _description = "Bureau"
    _order='name'

    name            = fields.Char('Bureau', required=True)
    commentaire     = fields.Text('Commentaire')


class is_type_ordinateur(models.Model):
    _name = "is.type.ordinateur"
    _description = "Type d'ordinateur"
    _order='name'

    name            = fields.Char("Type d'ordinateur", required=True)
    commentaire     = fields.Text('Commentaire')


class is_ordinateur(models.Model):
    _name = "is.ordinateur"
    _description = "Ordinateurs"
    _order='name'

    _sql_constraints = [('name_uniq','UNIQUE(name)', 'Ce code existe déjà')] 

    def _compute(self):
        for obj in self:
            obj.partage_nb          = len(obj.partage_ids)
            obj.suivi_sauvegarde_nb = len(obj.suivi_sauvegarde_ids)


    site_id              = fields.Many2one('is.site', 'Site', required=True)
    name                 = fields.Char('Nom du poste', required=True)
    type_ordinateur_id   = fields.Many2one('is.type.ordinateur', "Type d'ordinateur")
    bureau_id            = fields.Many2one('is.bureau', 'Bureau')
    service_id           = fields.Many2one('is.service', 'Service')
    utilisateur_id       = fields.Many2one('is.utilisateur', 'Utilisateur')
    date_achat           = fields.Date("Date d'achat")
    partage_ids          = fields.Many2many('is.partage' , 'is_ordinateur_partage_rel' , 'ordinateur_id','partage_id' , string="Partages", help=u"Ce champ est utilisé par le programme de sauvegarde des messageries" )
    partage_nb           = fields.Integer('Nombre de partages', compute='_compute', readonly=True, store=False)
    commentaire          = fields.Text('Commentaire')
    action_ids           = fields.One2many('is.action', 'ordinateur_id', u'Actions', readonly=True)
    sauvegarde_ids       = fields.One2many('is.save.mozilla', 'ordinateur_id', u'Sauvegardes', readonly=True)
    suivi_sauvegarde_ids = fields.One2many('is.suivi.sauvegarde', 'ordinateur_id', u'Suivi des sauvegardes', readonly=True)
    suivi_sauvegarde_nb  = fields.Integer('Nb suivi sauvegarde', compute='_compute', readonly=True, store=False)
    active               = fields.Boolean('Actif', default=True)

    glpi_name              = fields.Char('Nom du poste GLPI' , readonly=True)
    glpi_contact           = fields.Char('Utilisateur GLPI'  , readonly=True)
    glpi_serial            = fields.Char('N°série'      , readonly=True)
    glpi_os_license_number = fields.Char('Licence OS'   , readonly=True)
    glpi_os_licenseid      = fields.Char('Licence OS id', readonly=True)
    glpi_date_mod          = fields.Datetime('Date GLPI', readonly=True)
    glpi_operatingsystems  = fields.Char('Système'      , readonly=True)

    glpi_bios_date         = fields.Date('Date du bios', readonly=True)
    glpi_installationdate  = fields.Date("Date d'installation", readonly=True)
    glpi_remote_addr       = fields.Text('Adresse IP'      , readonly=True)
    glpi_adresse_ip_mac    = fields.Text('Adresse IP+MAC'  , readonly=True)
    glpi_winowner          = fields.Char('Administrateur'  , readonly=True)

    net_rpc_users          = fields.Char('net rpc users'   , readonly=True)
    net_rpc_admins         = fields.Char('net rpc admins'  , readonly=True)
    net_rpc_partages       = fields.Char('net rpc partages', readonly=True)


    def actualiser_glpi_action(self):
        uid=self._uid
        user=self.env['res.users'].browse(uid)
        glpi_host   = user.company_id.is_glpi_host
        glpi_user   = user.company_id.is_glpi_user
        glpi_passwd = user.company_id.is_glpi_passwd
        glpi_db     = user.company_id.is_glpi_db
        try:
           db = MySQLdb.connect(host=glpi_host, user=glpi_user, passwd=glpi_passwd, db=glpi_db)
        except MySQLdb.OperationalError:
           raise Warning(u"La connexion à GLPI a échouée !")
        

        #db = MySQLdb.connect(host=glpi_host, user=glpi_user, passwd=glpi_passwd, db=glpi_db)


        cur = db.cursor()
        nb=len(self)
        ct=0
        for obj in self:
            ct=ct+1
            name = obj.name.encode('ascii', 'ignore')

            _logger.info(str(ct)+u'/'+str(nb)+u' : Mise à jour GLPI '+name)

            SQL="""
                select
                    c.name,
                    c.contact,
                    c.serial,
                    '' os_license_number,
                    '' os_licenseid,
                    agents.last_contact,
                    concat(os.name,' ',v.name),
                    sp.name,
                    '' bios_date,
                    f.operatingsystem_installationdate,
                    f.remote_addr,
                    f.winowner
                from glpi_computers c inner join glpi_items_operatingsystems    i on c.id=i.items_id
                                      inner join glpi_operatingsystems         os on i.operatingsystems_id=os.id
                                      inner join glpi_operatingsystemversions   v on i.operatingsystemversions_id=v.id
                                      left outer join glpi_operatingsystemservicepacks sp on i.operatingsystemservicepacks_id=sp.id
                                      left outer join glpi_plugin_fusioninventory_inventorycomputercomputers f on f.computers_id=c.id
                                      left outer join glpi_plugin_fusioninventory_agents agents on c.id=agents.computers_id
                WHERE c.name=%s
            """

            cur.execute(SQL, [name])
            for row in cur.fetchall():
                obj.glpi_name              = row[0]
                obj.glpi_contact           = row[1]
                obj.glpi_serial            = row[2]
                obj.glpi_os_license_number = row[3]
                obj.glpi_os_licenseid      = row[4]
                obj.glpi_date_mod          = row[5]
                obj.glpi_operatingsystems  = (row[6] or '')+' '+(row[7] or '')
                if row[8]:
                    obj.glpi_bios_date     = row[8].strftime('%Y-%m-%d')  
                if row[9]:
                    obj.glpi_installationdate = row[9].strftime('%Y-%m-%d')  
                obj.glpi_remote_addr       = row[10]
                obj.glpi_winowner          = row[11]

    def actualiser_glpi_scheduler_action(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        self.actualiser_glpi_scheduler(cr, uid, context)


    def actualiser_glpi_scheduler(self):
        _logger.info("## Actualisation depuis GLPI - Début")
        ordinateurs=self.env['is.ordinateur'].search([])
        ordinateurs.actualiser_glpi_action()
        _logger.info("## Actualisation depuis GLPI - Fin")



