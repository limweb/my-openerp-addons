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
    'name': 'Ineco Quality Control/Assurance',
    'version': '0.1',
    'category': 'Extension',
    'description': """
        """,
    'author': 'INECO LIMITED PARTNERSHIP',
    'depends': ["base","product","stock"],
    'website': 'http://openerp.tititab.com',
    'update_xml': [
        "quality_sequence.xml",
        "quality_data.xml",
        "wizard/wizard_load_template_view.xml",
        "security.xml",
        "ineco_quality_view.xml",
        "product_view.xml",
        "stock_view.xml",
         ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
