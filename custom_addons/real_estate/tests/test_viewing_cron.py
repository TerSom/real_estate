from datetime import datetime, time, timedelta
from unittest.mock import patch

from odoo import fields
from odoo.addons.base.models.ir_cron import IrCron
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestViewingCron(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_agent = cls.env.ref('real_estate.group_real_estate_agent')
        cls.agent = cls.env['res.users'].create({
            'name': 'Viewing Cron Agent',
            'login': 'viewing_cron_agent',
            'group_ids': [(6, 0, [group_agent.id])],
        })
        cls.partner = cls.env['res.partner'].create({'name': 'Viewing Client'})
        cls.prop = cls.env['real.estate.property'].create({
            'name': 'Viewing Cron House',
            'expected_price': 120000.0,
            'agent_id': cls.agent.id,
            'state': 'listed',
        })

        tomorrow = fields.Date.today() + timedelta(days=1)
        day_after = tomorrow + timedelta(days=1)

        cls.viewing_tomorrow = cls.env['real.estate.viewing'].create({
            'property_id': cls.prop.id,
            'partner_id': cls.partner.id,
            'agent_id': cls.agent.id,
            'date_start': datetime.combine(tomorrow, time(10, 0)),
        })
        cls.viewing_cancelled = cls.env['real.estate.viewing'].create({
            'property_id': cls.prop.id,
            'partner_id': cls.partner.id,
            'agent_id': cls.agent.id,
            'date_start': datetime.combine(tomorrow, time(14, 0)),
        })
        cls.viewing_cancelled.action_cancelled()
        cls.viewing_later = cls.env['real.estate.viewing'].create({
            'property_id': cls.prop.id,
            'partner_id': cls.partner.id,
            'agent_id': cls.agent.id,
            'date_start': datetime.combine(day_after, time(10, 0)),
        })

    def test_cron_remind_upcoming_viewings(self):
        with patch.object(IrCron, '_commit_progress', return_value=float('inf')):
            self.env['real.estate.viewing']._cron_remind_upcoming_viewings()
            # Re-run to ensure duplicate activities are not created
            self.env['real.estate.viewing']._cron_remind_upcoming_viewings()

        self.assertEqual(len(self.viewing_tomorrow.activity_ids), 1)
        act = self.viewing_tomorrow.activity_ids[0]
        self.assertEqual(act.user_id, self.agent)
        self.assertEqual(act.summary, 'Upcoming Viewing Reminder')
        self.assertFalse(self.viewing_cancelled.activity_ids)
        self.assertFalse(self.viewing_later.activity_ids)

    def test_viewing_requires_listed_property(self):
        draft_prop = self.env['real.estate.property'].create({
            'name': 'Draft House',
            'expected_price': 100000.0,
            'agent_id': self.agent.id,
        })
        tomorrow = fields.Date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.env['real.estate.viewing'].create({
                'property_id': draft_prop.id,
                'partner_id': self.partner.id,
                'agent_id': self.agent.id,
                'date_start': datetime.combine(tomorrow, time(16, 0)),
            })
