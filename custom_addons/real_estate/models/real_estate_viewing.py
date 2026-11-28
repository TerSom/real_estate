from datetime import datetime, time, timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class RealEstateViewing(models.Model):
    _name = 'real.estate.viewing'
    _description = 'Real Estate Viewing'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    property_id = fields.Many2one(
        'real.estate.property',
        required=True,
        ondelete='cascade',
        domain=[('state', '=', 'listed')],
    )
    partner_id = fields.Many2one('res.partner',required=True)
    agent_id = fields.Many2one('res.users',default=lambda self: self.env.user)
    date_start = fields.Datetime(required=True, index=True)
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


    @api.constrains('property_id')
    def _check_property_listed(self):
        for record in self:
            if record.property_id and record.property_id.state != 'listed':
                raise ValidationError("Viewings can only be scheduled for listed properties.")

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

    @api.model
    def _cron_remind_upcoming_viewings(self, batch_size=100):
        tomorrow = fields.Date.today() + timedelta(days=1)
        start_dt = datetime.combine(tomorrow, time.min)
        end_dt = start_dt + timedelta(days=1)
        domain = [
            ('state', '=', 'scheduled'),
            ('date_start', '>=', start_dt),
            ('date_start', '<', end_dt),
        ]
        total = self.search_count(domain)
        if not total:
            return
        self.env['ir.cron']._commit_progress(remaining=total)
        last_id = 0
        while True:
            batch = self.search(
                domain + [('id', '>', last_id)],
                order='id',
                limit=batch_size,
            )
            if not batch:
                break
            last_id = batch[-1].id
            for viewing in batch:
                user_id = viewing.agent_id.id or viewing.property_id.agent_id.id
                if not user_id:
                    continue
                already_scheduled = any(
                    act.date_deadline == tomorrow
                    and act.summary == 'Upcoming Viewing Reminder'
                    for act in viewing.activity_ids
                )
                if already_scheduled:
                    continue
                viewing.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=tomorrow,
                    summary='Upcoming Viewing Reminder',
                    note=(
                        f"Viewing scheduled tomorrow for "
                        f"{viewing.property_id.display_name} with {viewing.partner_id.name}."
                    ),
                    user_id=user_id,
                )
            remaining_time = self.env['ir.cron']._commit_progress(processed=len(batch))
            if not remaining_time:
                break


