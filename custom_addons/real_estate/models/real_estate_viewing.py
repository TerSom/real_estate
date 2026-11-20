from odoo import models,fields,api
from datetime import timedelta
from odoo.exceptions import ValidationError, UserError

class RealEstateViewing(models.Model):
    _name = 'real.estate.viewing'
    _description = 'Real Estate Viewing'

    property_id = fields.Many2one('real.estate.property',required=True,ondelete='cascade')
    partner_id = fields.Many2one('res.partner',required=True)
    agent_id = fields.Many2one('res.users',default=lambda self: self.env.user)
    date_start = fields.Datetime(required=True)
    duration = fields.Float(default=1.0)
    date_stop = fields.Datetime(compute='_date_stop',store=True)
    state = fields.Selection([
        ('scheduled','Scheduled'),
        ('done','Done'),
        ('cancelled','Cancelled')
    ],default='scheduled',readonly=True,copy=False)
    note = fields.Text()

    @api.depends('date_start', 'duration')
    def _date_stop(self):
        for record in self:
            if record.date_start:
                record.date_stop = record.date_start + timedelta(hours=record.duration)
            else:
                record.date_stop = False


    @api.constrains('agent_id','date_start','date_stop')
    def _check_schedule_overlap(self):
        for record in self:
            if record.state == 'cancelled' or not record.date_start or not record.date_stop:
                continue
            overlap = self.search_count([
                ('id', '!=', record.id),
                ('agent_id', '=', record.agent_id.id),
                ('state', '!=', 'cancelled'),
                ('date_start', '<', record.date_stop),
                ('date_stop', '>', record.date_start),
            ])
            if overlap:
                raise ValidationError("Agent already has a viewing scheduled at this time.")

    @api.depends('property_id.name','partner_id.name')
    def _compute_display_name(self):
        for record in self:
            property_name = record.property_id.name or 'No Property'
            partner_name = record.partner_id.name or 'No Partner'

            record.display_name = f'{property_name} - {partner_name}'

    def action_done(self):
        for record in self:
            if record.state != 'scheduled':
                raise UserError("Only scheduled viewings can be marked as done.")
            record.state = 'done'

    def action_cancelled(self):
        for record in self:
            if record.state != 'scheduled':
                raise UserError("Only scheduled viewings can be cancelled.")
            record.state = 'cancelled'


