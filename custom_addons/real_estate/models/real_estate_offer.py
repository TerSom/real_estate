from odoo import models,fields,api
from datetime import timedelta
from odoo.exceptions import ValidationError,UserError

class RealEstateOffer(models.Model):
    _name = 'real.estate.offer'
    _description = 'Real Estate Offer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    property_id = fields.Many2one('real.estate.property', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', required=True)
    currency_id = fields.Many2one(related='property_id.currency_id', store=True)
    price = fields.Monetary(required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),
    ], default='draft', copy=False, readonly=True)
    validity_days = fields.Integer(default=7)
    date_deadline = fields.Date(
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline',
        store=True,
        index=True,
    )

    _min_price = models.Constraint(
        'CHECK(price > 0)',
        "Price must be greater than 0.",
    )

    @api.depends('create_date', 'validity_days')
    def _compute_date_deadline(self):
        for record in self:
            date = record.create_date.date() if record.create_date else fields.Date.today()
            record.date_deadline = date + timedelta(days=record.validity_days)

    def _inverse_date_deadline(self):
        for record in self:
            date = record.create_date.date() if record.create_date else fields.Date.today()
            record.validity_days = (record.date_deadline - date).days

    def action_accept(self):
        for record in self:
            prop = record.property_id
            if prop.state in ('sold', 'cancelled'):
                raise UserError("Cannot accept an offer on a sold or cancelled property.")
            if prop.offer_ids.filtered(lambda o: o.state == 'accepted'):
                raise UserError("This property already has an accepted offer.")
            record.state = 'accepted'
            prop.write({
                'buyer_id': record.partner_id.id,
                'selling_price': record.price,
            })
            prop.message_post(body=f"Offer from {record.partner_id.name} accepted at {record.price}")

    def action_refuse(self):
        for record in self:
            record.state = 'refused'

    @api.model_create_multi
    def create(self, vals_list):
        property_ids = [
            vals.get("property_id")
            for vals in vals_list
            if vals.get("property_id")
        ]

        if self.env["real.estate.offer"].search_count([
                ("property_id", "in", property_ids),
                ("state", "=", "accepted"),
            ]):
            raise ValidationError(
                "You cannot create a new offer after an offer has been accepted."
            )

        records = super().create(vals_list)
        records.property_id.state = 'listed'
        return records

    @api.model
    def _cron_expire_offer(self, batch_size=100):
        domain = [
            ('state', '=', 'draft'),
            ('date_deadline', '<', fields.Date.today()),
        ]
        total = self.search_count(domain)
        if not total:
            return
        self.env['ir.cron']._commit_progress(remaining=total)
        while True:
            batch = self.search(domain, order='property_id, id', limit=batch_size)
            if not batch:
                break
            batch.write({'state': 'refused'})
            for prop, offers in batch.grouped('property_id').items():
                count = len(offers)
                noun = "offer" if count == 1 else "offers"
                prop.message_post(
                    body=f"{count} expired draft {noun} automatically marked as refused."
                )
            remaining_time = self.env['ir.cron']._commit_progress(processed=len(batch))
            if not remaining_time:
                break