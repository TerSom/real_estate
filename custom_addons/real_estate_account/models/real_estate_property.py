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
        for record in self:
            record.invoice_count = len(record.invoice_ids)

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

        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        income_account = journal.default_account_id

        moves_vals = []
        prop_map = []

        for prop in self:
            if prop.invoice_id:
                continue

            moves_vals.append({
                'partner_id': prop.buyer_id.id,
                'move_type': 'out_invoice',
                'property_id': prop.id,
                'invoice_line_ids': [
                    Command.create({
                        'name': f"Property: {prop.name}",
                        'quantity': 1.0,
                        'price_unit': prop.selling_price,
                        'account_id': income_account.id if income_account else False,
                    }),
                ],
            })
            prop_map.append(prop)

        if moves_vals:
            created_moves = self.env['account.move'].sudo().create(moves_vals)
            for prop, move in zip(prop_map, created_moves):
                prop.invoice_id = move.id

        return res