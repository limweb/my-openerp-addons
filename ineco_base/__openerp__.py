# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 INECO LTD, PARTNERSHIP (<http://www.ineco.co.th>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Extension for Base Object',
    'version': '0.5',
    'category': 'Extension',
    'description': """
            1. This module will add TaxID on Partner for Thai Company.
            2. Change Current user company_id.
            3. Add uom_category_id in stock.inventory.
            4. Change Delivery state in done, cancel to draft state.
            5. Sale order Cancelling must be cancel all delivery order.
        """,
    'author': 'INECO LIMITED PARTNERSHIP',
    'depends': ["base","product","stock","purchase","sale","procurement","stock_planning"],
    'website': 'http://openerp.tititab.com',
    'update_xml': [
        "security.xml",
        "base_menu.xml",
        "partner_view.xml",
        "wizard_clearing_stock_view.xml",
        "wizard_split_view.xml",
        "wizard_physical_inventory_zero_view.xml",
        "stock_receive_card_view.xml",
        "stock_view.xml",
        "company_view.xml",
        "product_view.xml",
        "purchase_view.xml",
        "wizard/wizard_schedule_delivery_compute_view.xml",
        "report_data.xml",
        "wizard/wizard_stock_report_print_view.xml",
        "wizard/wizard_export_stock_counting_view.xml",
        "wizard/wizard_adjust_stock_report_view.xml",
        "wizard/wizard_insert_stock_report_view.xml",
        "stock_inventory_load_view.xml",
         ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
