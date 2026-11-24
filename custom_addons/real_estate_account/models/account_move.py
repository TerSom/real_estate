from odoo import models,fields,api

class AccountMove(models.Model):
    _inherit = 'account.move'

    property_id = fields.Many2one('real.estate.property', ondelete='restrict')
    