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
    'name': 'Ineco Logistic Module',
    'version': '0.1',
    'category': 'Extension',
    'description': """
        """,
    'author': 'INECO LIMITED PARTNERSHIP',
    'depends': ["ineco_base","stock"],
    'website': 'http://www.ineco.co.th',
    'update_xml': [
        'logistic_view.xml',
        'stock_view.xml',
        'security.xml',
        'ineco_logistic_data.xml',
        'wizard/wizard_ineco_logistic_report_delivery_pack_view.xml',
        'wizard/wizard_ineco_logistic_report_kitting_view.xml',
        'wizard/wizard_ineco_logistic_report_kitting_slip_view.xml',
        'wizard/wizard_ineco_logistic_report_dispatch_view.xml',
        'wizard/wizard_ineco_logistic_report_summary_view.xml',
         ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
