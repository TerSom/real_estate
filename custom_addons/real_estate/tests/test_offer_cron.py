from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.addons.base.models.ir_cron import IrCron
from odoo.tests.common import TransactionCase


class TestOfferCron(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Buyer Cron Test'})
        cls.prop_multi = cls.env['real.estate.property'].create({
            'name': 'Multi Offer Property',
            'expected_price': 100000.0,
        })
        cls.prop_keep = cls.env['real.estate.property'].create({
            'name': 'Accepted & Active Property',
            'expected_price': 150000.0,
        })

        past_date = fields.Date.today() - timedelta(days=1)
        future_date = fields.Date.today() + timedelta(days=5)

        cls.expired_1 = cls.env['real.estate.offer'].create({
            'property_id': cls.prop_multi.id,
            'partner_id': cls.partner.id,
            'price': 80000.0,
            'date_deadline': past_date,
        })
        cls.expired_2 = cls.env['real.estate.offer'].create({
            'property_id': cls.prop_multi.id,
            'partner_id': cls.partner.id,
            'price': 85000.0,
            'date_deadline': past_date,
        })
        cls.expired_3 = cls.env['real.estate.offer'].create({
            'property_id': cls.prop_multi.id,
            'partner_id': cls.partner.id,
            'price': 90000.0,
            'date_deadline': past_date,
        })
        cls.active_offer = cls.env['real.estate.offer'].create({
            'property_id': cls.prop_multi.id,
            'partner_id': cls.partner.id,
            'price': 95000.0,
            'date_deadline': future_date,
        })

        cls.accepted_expired = cls.env['real.estate.offer'].create({
            'property_id': cls.prop_keep.id,
            'partner_id': cls.partner.id,
            'price': 140000.0,
            'date_deadline': past_date,
        })
        cls.accepted_expired.action_accept()

    def test_cron_expire_offer_batch_and_chatter(self):
        before_msg_count = len(self.prop_multi.message_ids)
        with patch.object(IrCron, '_commit_progress', return_value=float('inf')):
            self.env['real.estate.offer']._cron_expire_offer(batch_size=2)

        self.assertEqual(self.expired_1.state, 'refused')
        self.assertEqual(self.expired_2.state, 'refused')
        self.assertEqual(self.expired_3.state, 'refused')
        self.assertEqual(self.active_offer.state, 'draft')
        self.assertEqual(self.accepted_expired.state, 'accepted')
        self.assertEqual(self.prop_multi.state, 'listed')

        new_msgs = self.prop_multi.message_ids[:-before_msg_count] if before_msg_count else self.prop_multi.message_ids
        # batch_size=2 splits 3 offers across 2 batches -> at most 2 messages; with default batch_size=100 -> 1 message.
        self.assertTrue(any('expired draft' in (m.body or '') for m in new_msgs))

    def test_cron_expire_offer_single_message_per_property(self):
        before_msg_count = len(self.prop_multi.message_ids)
        with patch.object(IrCron, '_commit_progress', return_value=float('inf')):
            self.env['real.estate.offer']._cron_expire_offer()

        self.assertEqual(len(self.prop_multi.message_ids) - before_msg_count, 1)
        self.assertIn('3 expired draft offers', self.prop_multi.message_ids[0].body)
