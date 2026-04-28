from odoo import models, api, exceptions

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['groups_id'] = [(6, 0, [])]
        return super().create(vals_list)