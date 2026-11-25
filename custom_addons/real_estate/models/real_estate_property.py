from odoo import fields,models,api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError,UserError

class RealEstateProperty(models.Model):
    _name = 'real.estate.property'
    _description = 'Real Estate Property'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    description = fields.Text()
    postcode = fields.Char()
    expected_price = fields.Monetary(required=True,tracking=True)
    bedrooms = fields.Integer(default=2)
    living_area = fields.Integer()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    total_land_area = fields.Integer(compute='_total_land_area')
    date_availability = fields.Date(copy=False, default=lambda self: fields.Date.today() + relativedelta(months=3),)
    state = fields.Selection([
        ('draft','Draft'),
        ('listed','Listed'),
        ('sold','Sold'),
        ('cancelled','Cancelled')
    ],default='draft',required=True,readonly=True,tracking=True)
    active = fields.Boolean(default=True)
    best_price = fields.Monetary(compute='_compute_best_price')
    selling_price = fields.Monetary(readonly=True,copy=False,tracking=True)
    code = fields.Char(string='Reference', readonly=True, copy=False, default='New', index=True)
    agent_id = fields.Many2one('res.users',string='Agent', default=lambda self: self.env.user, copy=False)
    buyer_id = fields.Many2one('res.partner',readonly=True,copy=False,tracking=True)
    currency_id = fields.Many2one('res.currency',required=True,store=True,default=lambda self: self.env.company.currency_id)
    type_id = fields.Many2one('real.estate.type',ondelete='restrict')
    tag_ids = fields.Many2many('real.estate.tag')
    offer_ids = fields.One2many('real.estate.offer','property_id')
    viewing_ids = fields.One2many('real.estate.viewing','property_id')
    viewing_count = fields.Integer(compute='_compute_viewing_count')

    _code_unique = models.Constraint('UNIQUE(code)','Reference must be unique.')

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.code}] {record.name}" if record.code else record.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code','New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('real.estate.property') or 'New'
        return super().create(vals_list)

    @api.depends('offer_ids.price')
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offer_ids.mapped('price'),default=0.0)

    @api.depends('viewing_ids')
    def _compute_viewing_count(self):
        for record in self:
            record.viewing_count = len(record.viewing_ids)
    
    @api.onchange('garden')
    def onchange_garden(self):
        for record in self:
            if not record.garden:
                record.garden_area = 0
    
    @api.depends('living_area','garden_area')
    def _total_land_area(self):
        for record in self:
            record.total_land_area = record.living_area + record.garden_area

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

    def action_view_viewings(self):
        self.ensure_one()
        return {
            'name': 'Viewings',
            'type': 'ir.actions.act_window',
            'res_model': 'real.estate.viewing',
            'view_mode': 'calendar,list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }
