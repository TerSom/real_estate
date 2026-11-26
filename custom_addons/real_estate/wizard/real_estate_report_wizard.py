import base64
import io
import xlsxwriter
from odoo import fields, models


class RealEstateReportWizard(models.TransientModel):
    _name = 'real.estate.report.wizard'
    _description = 'Real Estate Report Wizard'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('listed', 'Listed'),
        ('sold', 'Sold'),
        ('cancelled', 'Cancelled'),
    ], string='Status')
    type_id = fields.Many2one('real.estate.type', string='Property Type')
    agent_id = fields.Many2one('res.users', string='Agent')
    date_from = fields.Date(string='Available From')
    date_to = fields.Date(string='Available To')

    file_data = fields.Binary(string='File', readonly=True)
    file_name = fields.Char(string='File Name')

    def _get_properties(self):
        active_ids = self.env.context.get('active_ids')
        if active_ids and self.env.context.get('active_model') == 'real.estate.property':
            return self.env['real.estate.property'].browse(active_ids)

        domain = []
        if self.state:
            domain.append(('state', '=', self.state))
        if self.type_id:
            domain.append(('type_id', '=', self.type_id.id))
        if self.agent_id:
            domain.append(('agent_id', '=', self.agent_id.id))
        if self.date_from:
            domain.append(('date_availability', '>=', self.date_from))
        if self.date_to:
            domain.append(('date_availability', '<=', self.date_to))

        # Do not use sudo(); regular env enforces ir.access permissions
        return self.env['real.estate.property'].search(domain)

    def action_generate(self):
        self.ensure_one()
        properties = self._get_properties()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        formats = {
            'header': workbook.add_format({
                'bold': True,
                'bg_color': '#183E34',
                'font_color': '#FFFFFF',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
            }),
            'date': workbook.add_format({
                'num_format': 'yyyy-mm-dd',
                'align': 'center',
            }),
            'money': workbook.add_format({
                'num_format': '#,##0.00',
            }),
            'center': workbook.add_format({
                'align': 'center',
            }),
            'total_money': workbook.add_format({
                'num_format': '#,##0.00',
                'bold': True,
                'top': 1,
                'bottom': 6,
            }),
            'total_label': workbook.add_format({
                'bold': True,
                'top': 1,
                'bottom': 6,
                'align': 'right',
            }),
            'total_border': workbook.add_format({
                'top': 1,
                'bottom': 6,
            }),
        }

        self._write_properties_sheet(workbook, properties, formats)
        self._write_offers_sheet(workbook, properties, formats)
        workbook.close()

        filename = f"property_report_{fields.Date.today()}.xlsx"
        self.write({
            'file_data': base64.b64encode(output.getvalue()).decode('utf-8'),
            'file_name': filename,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content?model={self._name}&id={self.id}&field=file_data&filename_field=file_name&download=true",
            'target': 'self',
        }

    def _write_properties_sheet(self, workbook, properties, formats):
        ws = workbook.add_worksheet('Properties')
        headers = [
            'Reference', 'Property Name', 'Type', 'Agent', 'Status',
            'Expected Price', 'Best Offer', 'Selling Price', 'Buyer',
            'Tags', 'Available From',
        ]
        ws.write_row(0, 0, headers, formats['header'])

        state_dict = dict(self.env['real.estate.property']._fields['state']._description_selection(self.env))
        col_widths = [len(h) for h in headers]

        row = 1
        for prop in properties:
            state_label = state_dict.get(prop.state, prop.state or '')
            tags_str = ", ".join(prop.tag_ids.mapped('name'))

            row_data = [
                prop.code or '',
                prop.name or '',
                prop.type_id.name or '',
                prop.agent_id.name or '',
                state_label,
                prop.expected_price or 0.0,
                prop.best_price or 0.0,
                prop.selling_price or 0.0,
                prop.buyer_id.name or '',
                tags_str,
                prop.date_availability,
            ]

            ws.write(row, 0, row_data[0])
            ws.write(row, 1, row_data[1])
            ws.write(row, 2, row_data[2])
            ws.write(row, 3, row_data[3])
            ws.write(row, 4, row_data[4], formats['center'])
            ws.write(row, 5, row_data[5], formats['money'])
            ws.write(row, 6, row_data[6], formats['money'])
            ws.write(row, 7, row_data[7], formats['money'])
            ws.write(row, 8, row_data[8])
            ws.write(row, 9, row_data[9])
            if row_data[10]:
                ws.write(row, 10, row_data[10], formats['date'])
            else:
                ws.write(row, 10, '')

            for c, val in enumerate(row_data):
                val_str = str(val or '')
                col_widths[c] = max(col_widths[c], len(val_str))
            row += 1

        # Summary total row with Excel formula
        if row > 1:
            for c in range(len(headers)):
                if c < 4:
                    ws.write(row, c, '', formats['total_border'])
                elif c == 4:
                    ws.write(row, c, 'Total', formats['total_label'])
                elif c == 5:
                    ws.write_formula(row, c, f"=SUM(F2:F{row})", formats['total_money'])
                elif c == 6:
                    ws.write_formula(row, c, f"=SUM(G2:G{row})", formats['total_money'])
                elif c == 7:
                    ws.write_formula(row, c, f"=SUM(H2:H{row})", formats['total_money'])
                else:
                    ws.write(row, c, '', formats['total_border'])

        ws.freeze_panes(1, 0)
        max_row = max(row - 1, 1)
        ws.autofilter(0, 0, max_row, len(headers) - 1)

        for i, width in enumerate(col_widths):
            ws.set_column(i, i, max(width + 3, 12))

    def _write_offers_sheet(self, workbook, properties, formats):
        ws = workbook.add_worksheet('Offers')
        headers = [
            'Property Code', 'Property Name', 'Buyer', 'Price',
            'Status', 'Validity (Days)', 'Deadline',
        ]
        ws.write_row(0, 0, headers, formats['header'])

        offer_state_dict = dict(self.env['real.estate.offer']._fields['state']._description_selection(self.env))
        col_widths = [len(h) for h in headers]

        row = 1
        # Loop properties.offer_ids with batch prefetching
        for prop in properties:
            for offer in prop.offer_ids:
                offer_state_label = offer_state_dict.get(offer.state, offer.state or '')
                row_data = [
                    prop.code or '',
                    prop.name or '',
                    offer.partner_id.name or '',
                    offer.price or 0.0,
                    offer_state_label,
                    offer.validity_days or 0,
                    offer.date_deadline,
                ]

                ws.write(row, 0, row_data[0])
                ws.write(row, 1, row_data[1])
                ws.write(row, 2, row_data[2])
                ws.write(row, 3, row_data[3], formats['money'])
                ws.write(row, 4, row_data[4], formats['center'])
                ws.write(row, 5, row_data[5], formats['center'])
                if row_data[6]:
                    ws.write(row, 6, row_data[6], formats['date'])
                else:
                    ws.write(row, 6, '')

                for c, val in enumerate(row_data):
                    val_str = str(val or '')
                    col_widths[c] = max(col_widths[c], len(val_str))
                row += 1

        # Summary total row with Excel formula
        if row > 1:
            for c in range(len(headers)):
                if c < 2:
                    ws.write(row, c, '', formats['total_border'])
                elif c == 2:
                    ws.write(row, c, 'Total', formats['total_label'])
                elif c == 3:
                    ws.write_formula(row, c, f"=SUM(D2:D{row})", formats['total_money'])
                else:
                    ws.write(row, c, '', formats['total_border'])

        ws.freeze_panes(1, 0)
        max_row = max(row - 1, 1)
        ws.autofilter(0, 0, max_row, len(headers) - 1)

        for i, width in enumerate(col_widths):
            ws.set_column(i, i, max(width + 3, 12))
