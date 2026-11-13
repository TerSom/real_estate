from odoo import models,fields,api

class RealEstateTag(models.Model):
    _name = 'real.estate.tag'
    _description = 'Real Estate Tag'
    _order = 'name'

    name = fields.Char(required=True)
    color = fields.Integer()

    _sql_constraints = [
            ('name_unique', 'UNIQUE(name)', 'Name must be unique.')
        ]
    