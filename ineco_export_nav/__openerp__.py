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
    'name': 'Ineco Export CSV for Microsoft NAV',
    'version': '0.1',
    'category': 'Extension',
    'description': """
        This module will export data to csv format by NAV (Data Ports). 
        """,
    'author': 'INECO LIMITED PARTNERSHIP',
    'depends': ["base","purchase","sale","account","hr"],
    'website': 'http://openerp.tititab.com',
    'update_xml': [
        "ineco_export_view.xml",
        "export_data.xml",
        "purchase_view.xml",
        "sale_view.xml",
        "account_view.xml",
        "partner_view.xml",
        "department_view.xml",
        "users_view.xml",
        "pretty_cash_view.xml",
        "company_view.xml",
        "ineco_asset_view.xml",
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
