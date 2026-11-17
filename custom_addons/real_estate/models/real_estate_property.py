from odoo import fields,models,api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError,UserError

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
    ],default='draft',required=True,readonly=True)
    active = fields.Boolean(default=True)
    best_price = fields.Float(compute='_compute_best_price')
    buyer_id = fields.Many2one('res.partner',readonly=True,copy=False)
    selling_price = fields.Float(readonly=True,copy=False)
    type_id = fields.Many2one('real.estate.type',ondelete='restrict')
    tag_ids = fields.Many2many('real.estate.tag')
    offer_ids = fields.One2many('real.estate.offer','property_id')

    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offer_ids.mapped('price'),default=0.0)

    def action_sold(self):
        for record in self:
            if record.state == 'cancelled':
                raise UserError("Cancelled property cannot be sold.")
            if not record.offer_ids.filtered(lambda o: o.state == 'accepted'):
                raise UserError("No accepted offer. Accept an offer first.")
            record.state = 'sold'


    def action_cancel(self):
        for record in self:
            if record.state == 'sold':
                raise UserError("Sold property cannot be cancelled.")
            record.offer_ids.filtered(lambda o: o.state == 'accepted').write({'state': 'refused'})
            record.write({
                'state': 'cancelled',
                'buyer_id': False,
                'selling_price': 0.0,
            })
