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
    'name': 'Extension for Purchase Requisition',
    'version': '1',
    'category': 'Extension',
    'description': """This module will access right for default purchase requisition user/manager""",
    'author': 'INECO LIMITED PARTNERSHIP',
    'depends': ["purchase","purchase_requisition"],
    'website': 'http://openerp.tititab.com',
    'update_xml': [
        'security/ir.model.access.csv',
        'security/purchase_requisition_security.xml',
        'purchase_requisition_view.xml'
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
