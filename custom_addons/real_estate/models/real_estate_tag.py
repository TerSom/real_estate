from odoo import models,fields,api

class RealEstateTag(models.Model):
    _name = 'real.estate.tag'
    _description = 'Real Estate Tag'
    _order = 'name'

    name = fields.Char(required=True)
    color = fields.Integer()

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        "Name must be unique.",
    )
    