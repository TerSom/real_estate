from odoo import fields,models,api
from dateutil.relativedelta import relativedelta

class RealEstateProperty(models.Model):
    _name = 'real.estate.property'
    _description = 'Real Estate Property'

    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()
    expected_price = fields.Float(required=True)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    garden = fields.Boolean()
    date_availability = fields.Date(copy=False, default=lambda self: fields.Date.today() + relativedelta(months=3),)
    state = fields.Selection([
        ('draft','Draft'),
        ('listed','Listed'),
        ('sold','Sold'),
        ('cancelled','Cancelled')
    ],default='draft',required=True)
    active = fields.Boolean(default=True)