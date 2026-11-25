from odoo import models,fields,api,Command
from odoo.exceptions import UserError

class RealEstateProperty(models.Model):
    _inherit = 'real.estate.property'

    invoice_ids = fields.One2many('account.move', 'property_id', string='Invoices')
    invoice_id = fields.Many2one('account.move', string="Invoice", readonly=True, copy=False)
    invoice_count = fields.Integer(compute='_compute_invoice_count')
    commission_rate = fields.Float(default=2.5)

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        counts = dict(self.env['account.move'].sudo()._read_group(
            [('property_id', 'in', self.ids)], ['property_id'], ['__count'],
        ))
        for record in self:
            record.invoice_count = counts.get(record, 0)

    def action_view_invoice(self):
        self.ensure_one()
        action = {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {
                'default_property_id': self.id,
                'default_move_type': 'out_invoice',
            },
        }
        if len(self.invoice_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.invoice_ids.id,
            })
        return action

    def action_sold(self):
        res = super().action_sold()
        Move = self.env['account.move'].sudo()
        already = Move.search([('property_id', 'in', self.ids)]).property_id

        moves_vals = []
        for prop in self - already:
            moves_vals.append({
                'move_type': 'out_invoice',
                'partner_id': prop.buyer_id.id,
                'property_id': prop.id,
                'invoice_origin': prop.name,
                'invoice_line_ids': [Command.create({
                    'name': f"Property: {prop.name}",
                    'quantity': 1.0,
                    'price_unit': prop.selling_price,
                })],
            })
            if prop.agent_id and prop.commission_rate > 0:
                moves_vals.append({
                    'move_type': 'in_invoice',
                    'partner_id': prop.agent_id.partner_id.id,
                    'property_id': prop.id,
                    'invoice_origin': prop.name,
                    'invoice_line_ids': [Command.create({
                        'name': f"Commission: {prop.name} ({prop.commission_rate}%)",
                        'quantity': 1.0,
                        'price_unit': prop.selling_price * prop.commission_rate / 100.0,
                    })],
                })
        if moves_vals:
            Move.create(moves_vals)
        return res