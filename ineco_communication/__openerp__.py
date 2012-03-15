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
    'name': 'Extension for Internal Communication by Email, Request',
    'version': '0.1',
    'category': 'Extension',
    'description': """
            This module will create email communication or request by purchase requisition or purchase order.
            You must have 1 email account for communication by set email account in email-template and
            Verify that account and set name(description)-> email-agent
        """,
    'author': 'INECO LIMITED PARTNERSHIP',
    'depends': ["purchase","purchase_requisition","email_template"],
    'website': 'http://openerp.tititab.com',
    'update_xml': [
        'security/ir.model.access.csv',
        'security/ineco_communication_security.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
