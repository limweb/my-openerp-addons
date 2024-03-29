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
    'name': 'Sales Analytic Distribution Management',
    'version': '1.0',
    'category': 'Sales',
    'description': """
The base module to manage analytic distribution and sales orders.
=================================================================
    """,
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'images': ['images/sale_order_analytic_account.jpeg', 'images/sales_order_line.jpeg'],
    'depends': ['sale', 'account_analytic_plans'],
    'init_xml': [],
    'update_xml': ['sale_analytic_plans_view.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
    'certificate': '0066055860861',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
