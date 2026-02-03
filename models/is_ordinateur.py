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

    glpi_id_ordinateur           = fields.Integer('ID ordinateur GLPI', readonly=True)
    glpi_nom_ordinateur          = fields.Char('Nom ordinateur GLPI', readonly=True)
    glpi_numero_serie            = fields.Char('N° série', readonly=True)
    glpi_fabricant               = fields.Char('Fabricant', readonly=True)
    glpi_systeme_exploitation    = fields.Char('Système exploitation', readonly=True)
    glpi_version_os              = fields.Char('Version OS', readonly=True)
    glpi_version_bios            = fields.Char('Version BIOS', readonly=True)
    glpi_date_bios               = fields.Date('Date BIOS', readonly=True)
    glpi_adresses_mac            = fields.Char('Adresses MAC', readonly=True)
    glpi_usager                  = fields.Char('Usager', readonly=True)
    glpi_utilisateur_affecte     = fields.Char('Utilisateur affecté', readonly=True)
    glpi_adresse_publique        = fields.Char('Adresse publique', readonly=True)
    glpi_version_agent           = fields.Char('Version agent', readonly=True)
    glpi_dernier_contact         = fields.Datetime('Dernier contact', readonly=True)

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


        cur = db.cursor(MySQLdb.cursors.DictCursor)
        nb=len(self)
        ct=0
        for obj in self:
            ct=ct+1
            name = obj.name

            _logger.info(str(ct)+u'/'+str(nb)+u' : Mise à jour GLPI '+name)

            SQL="""
                SELECT 
                    c.id AS id_ordinateur,
                    c.name AS nom_ordinateur,
                    c.serial AS numero_serie,
                    m.name AS fabricant,
                    os.name AS systeme_exploitation,
                    osv.name AS version_os,
                    fw.designation AS version_bios,
                    fw.date AS date_bios,
                    GROUP_CONCAT(DISTINCT np.mac SEPARATOR ', ') AS adresses_mac,
                    c.contact AS usager,
                    CONCAT(u.firstname, ' ', u.realname) AS utilisateur_affecte,
                    a.remote_addr AS adresse_publique,
                    a.version AS version_agent,
                    a.last_contact AS dernier_contact
                FROM glpi_computers AS c
                LEFT JOIN glpi_agents AS a ON (a.items_id = c.id AND a.itemtype = 'Computer')
                LEFT JOIN glpi_manufacturers AS m ON c.manufacturers_id = m.id
                LEFT JOIN glpi_items_operatingsystems AS ios ON (ios.items_id = c.id AND ios.itemtype = 'Computer')
                LEFT JOIN glpi_operatingsystems AS os ON ios.operatingsystems_id = os.id
                LEFT JOIN glpi_operatingsystemversions AS osv ON ios.operatingsystemversions_id = osv.id
                LEFT JOIN glpi_items_devicefirmwares AS ifw ON (ifw.items_id = c.id AND ifw.itemtype = 'Computer' AND ifw.is_deleted = 0)
                LEFT JOIN glpi_devicefirmwares AS fw ON ifw.devicefirmwares_id = fw.id
                LEFT JOIN glpi_networkports AS np ON (np.items_id = c.id AND np.itemtype = 'Computer' AND np.is_deleted = 0)
                LEFT JOIN glpi_users AS u ON c.users_id = u.id
                WHERE c.is_deleted = 0
                    AND c.is_template = 0
                    AND c.name = %s
                GROUP BY c.id, c.name, c.serial, c.otherserial, c.contact, m.name, os.name, osv.name, fw.designation, fw.date, u.firstname, u.realname, a.remote_addr, a.name, a.version, a.last_contact
                ORDER BY c.name;
            """

            cur.execute(SQL, [name])
            for row in cur.fetchall():
                obj.glpi_id_ordinateur        = row['id_ordinateur']
                obj.glpi_nom_ordinateur       = row['nom_ordinateur']
                obj.glpi_numero_serie         = row['numero_serie']
                obj.glpi_fabricant            = row['fabricant']
                obj.glpi_systeme_exploitation = row['systeme_exploitation']
                obj.glpi_version_os           = row['version_os']
                obj.glpi_version_bios         = row['version_bios']
                if row['date_bios']:
                    obj.glpi_date_bios        = row['date_bios'].strftime('%Y-%m-%d')
                obj.glpi_adresses_mac         = row['adresses_mac']
                obj.glpi_usager               = row['usager']
                obj.glpi_utilisateur_affecte  = row['utilisateur_affecte']
                obj.glpi_adresse_publique     = row['adresse_publique']
                obj.glpi_version_agent        = row['version_agent']
                obj.glpi_dernier_contact      = row['dernier_contact']





    def actualiser_glpi_scheduler_action(self, cr, uid, use_new_cursor=False, company_id = False, context=None):
        self.actualiser_glpi_scheduler(cr, uid, context)


    def actualiser_glpi_scheduler(self):
        _logger.info("## Actualisation depuis GLPI - Début")
        ordinateurs=self.env['is.ordinateur'].search([])
        ordinateurs.actualiser_glpi_action()
        _logger.info("## Actualisation depuis GLPI - Fin")



