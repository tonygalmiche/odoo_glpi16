from odoo import models, api, exceptions

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        # # ID des groupes
        # portal_group = self.env.ref('base.group_portal').id
        # internal_group = self.env.ref('base.group_user').id
        # # Corriger les groupes à la volée
        # if 'groups_id' in vals:
        #     command = vals['groups_id']
        #     if isinstance(command, list) and command and command[0] == 6:
        #         print('TEST 1',command)
        #         group_ids = command[2]
        #         if internal_group in group_ids:
        #             group_ids.remove(internal_group)
        #         if portal_group not in group_ids:
        #             group_ids.append(portal_group)
        #         vals['groups_id'] = [(6, 0, group_ids)]
        # else:
        #     vals['groups_id'] = [(6, 0, [portal_group])]
        vals['groups_id'] = [(6, 0, [])]
        return super().create(vals)