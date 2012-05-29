# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': 'Extension for SR Advance Co.,Ltd.',
    'version': '0.10',
    'category': 'Extension',
    'description': """This module will add some new requirement for SR Advance Co.,Ltd.""",
    'author': 'INECO',
    'depends': ['product','sale','sale_order_dates','purchase_requisition','mrp','ineco_base'],
    'website': 'http://openerp.tititab.com',
    'update_xml': [
        'security/sradvance_security.xml',
        'create_cost_line_wizard.xml',
        'wizard_find_schedule_finish_date.xml',
        'thick_view.xml',
        'product_view.xml',
        'sale_view.xml',
        'security/ir.model.access.csv',
        'stock_view.xml',
        'mrp_view.xml',
        'purchase_requisition_view.xml',
        'wizard/report_workorder_view.xml',
        'mrp_workflow.xml',
        'wizard/wizard_force_production_view.xml',
        'invoice_view.xml',
#        'purchase_view.xml',
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
