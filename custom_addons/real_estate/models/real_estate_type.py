from odoo import models,fields,api

class RealEstateType(models.Model):
    _name = 'real.estate.type'
    _description = 'Real Estate Type'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    property_ids = fields.One2many('real.estate.property','type_id')

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Name must be unique.')
    ]
