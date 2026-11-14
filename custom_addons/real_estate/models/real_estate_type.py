from odoo import models,fields,api

class RealEstateType(models.Model):
    _name = 'real.estate.type'
    _description = 'Real Estate Type'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    property_ids = fields.One2many('real.estate.property','type_id')
    property_count = fields.Integer(string='Property Count', compute="_compute_property_count")

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Name must be unique.')
    ]


    @api.depends('property_ids')
    def _compute_property_count(self):
        for record in self:
            record.property_count = len(record.property_ids)

    def action_view_properties(self):
        self.ensure_one()
        return {
            'name': 'View Real Estate Property',
            'type': 'ir.actions.act_window',
            'res_model': 'real.estate.property',
            'view_mode': 'list,form',
            'domain': [('type_id', '=', self.id)],
            'context': {
                'default_type_id': self.id,
            },
        }
