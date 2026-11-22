from odoo import models,fields,api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    offer_ids = fields.One2many('real.estate.offer','partner_id')
    offer_count = fields.Integer(compute='_compute_offer_count')
    viewing_ids = fields.One2many('real.estate.viewing','partner_id')
    viewing_count = fields.Integer(compute='_compute_viewing_count')

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)

    @api.depends('viewing_ids')
    def _compute_viewing_count(self):
        for record in self:
            record.viewing_count = len(record.viewing_ids)

    def action_view_offer(self):
        self.ensure_one()
        return {
            'name': 'Offer',
            'type': 'ir.actions.act_window',
            'res_model': 'real.estate.offer',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)]
        }
    def action_view_viewing(self):
        self.ensure_one()
        return {
            'name': 'viewing',
            'type': 'ir.actions.act_window',
            'res_model': 'real.estate.viewing',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)]
        }

