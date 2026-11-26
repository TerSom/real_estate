import io
import zipfile
import openpyxl
from odoo.tests.common import TransactionCase


class TestReportWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_agent = cls.env.ref('real_estate.group_real_estate_agent')
        cls.group_manager = cls.env.ref('real_estate.group_real_estate_manager')

        cls.agent_1 = cls.env['res.users'].create({
            'name': 'Agent One',
            'login': 'agent_one_wizard',
            'group_ids': [(6, 0, [cls.group_agent.id])],
        })
        cls.agent_2 = cls.env['res.users'].create({
            'name': 'Agent Two',
            'login': 'agent_two_wizard',
            'group_ids': [(6, 0, [cls.group_agent.id])],
        })
        cls.manager = cls.env['res.users'].create({
            'name': 'Manager One',
            'login': 'manager_one_wizard',
            'group_ids': [(6, 0, [cls.group_manager.id])],
        })

        # Property 1 owned by Agent 1 (state: sold)
        cls.prop_1 = cls.env['real.estate.property'].create({
            'name': 'Agent 1 Sold Villa',
            'expected_price': 200000.0,
            'agent_id': cls.agent_1.id,
        })
        offer_1 = cls.env['real.estate.offer'].create({
            'property_id': cls.prop_1.id,
            'partner_id': cls.env.user.partner_id.id,
            'price': 190000.0,
        })
        offer_1.action_accept()
        cls.prop_1.action_sold()

        # Property 2 owned by Agent 2 (state: draft)
        cls.prop_2 = cls.env['real.estate.property'].create({
            'name': 'Agent 2 Draft Apartment',
            'expected_price': 100000.0,
            'agent_id': cls.agent_2.id,
        })

    def _get_bytes(self, wizard):
        if hasattr(wizard.file_data, 'content'):
            return wizard.file_data.content
        return bytes(wizard.file_data)

    def test_01_empty_filter_generates_valid_xlsx(self):
        """Wizard with empty filter produces a valid xlsx zip file."""
        wizard = self.env['real.estate.report.wizard'].create({})
        res = wizard.action_generate()
        self.assertEqual(res['type'], 'ir.actions.act_url')
        self.assertTrue(wizard.file_data)

        raw_bytes = self._get_bytes(wizard)
        self.assertTrue(zipfile.is_zipfile(io.BytesIO(raw_bytes)))

        wb = openpyxl.load_workbook(io.BytesIO(raw_bytes))
        self.assertIn('Properties', wb.sheetnames)
        self.assertIn('Offers', wb.sheetnames)

    def test_02_filter_sold_only_includes_sold_properties(self):
        """Filter state='sold' includes only sold properties."""
        wizard = self.env['real.estate.report.wizard'].create({
            'state': 'sold',
        })
        wizard.action_generate()

        raw_bytes = self._get_bytes(wizard)
        wb = openpyxl.load_workbook(io.BytesIO(raw_bytes))
        ws = wb['Properties']

        # Header is row 1, data rows follow. If there is a total row, it has 'Total' in col 5.
        sold_names = []
        for row in range(2, ws.max_row + 1):
            cell_status = ws.cell(row=row, column=5).value
            cell_name = ws.cell(row=row, column=2).value
            if cell_status == 'Total':
                continue
            if cell_status:
                self.assertEqual(cell_status, 'Sold')
                sold_names.append(cell_name)

        self.assertIn(self.prop_1.name, sold_names)
        self.assertNotIn(self.prop_2.name, sold_names)

    def test_03_agent_only_sees_own_properties(self):
        """Agent user only exports their own properties due to ir.access, Manager sees all."""
        # Run as Agent 1
        wizard_agent = self.env['real.estate.report.wizard'].with_user(self.agent_1).create({})
        wizard_agent.action_generate()

        raw_agent = self._get_bytes(wizard_agent)
        wb_agent = openpyxl.load_workbook(io.BytesIO(raw_agent))
        ws_agent = wb_agent['Properties']

        agent_prop_names = [
            ws_agent.cell(row=r, column=2).value
            for r in range(2, ws_agent.max_row + 1)
            if ws_agent.cell(row=r, column=5).value != 'Total'
        ]
        self.assertIn(self.prop_1.name, agent_prop_names)
        self.assertNotIn(self.prop_2.name, agent_prop_names)

        # Run as Manager
        wizard_mgr = self.env['real.estate.report.wizard'].with_user(self.manager).create({})
        wizard_mgr.action_generate()

        raw_mgr = self._get_bytes(wizard_mgr)
        wb_mgr = openpyxl.load_workbook(io.BytesIO(raw_mgr))
        ws_mgr = wb_mgr['Properties']

        mgr_prop_names = [
            ws_mgr.cell(row=r, column=2).value
            for r in range(2, ws_mgr.max_row + 1)
            if ws_mgr.cell(row=r, column=5).value != 'Total'
        ]
        self.assertIn(self.prop_1.name, mgr_prop_names)
        self.assertIn(self.prop_2.name, mgr_prop_names)

    def test_04_active_ids_exports_only_selected_properties(self):
        """When opened from list view selection, only selected active_ids are exported."""
        wizard = self.env['real.estate.report.wizard'].with_context(
            active_ids=[self.prop_2.id],
            active_model='real.estate.property',
        ).create({})
        wizard.action_generate()

        raw_bytes = self._get_bytes(wizard)
        wb = openpyxl.load_workbook(io.BytesIO(raw_bytes))
        ws = wb['Properties']

        exported_names = [
            ws.cell(row=r, column=2).value
            for r in range(2, ws.max_row + 1)
            if ws.cell(row=r, column=5).value != 'Total'
        ]
        self.assertEqual(exported_names, [self.prop_2.name])
