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
    'name': 'Ineco Attachment Utility',
    'version': '0.2',
    'category': 'Extension',
    'description': """
This module will change attachment data from binary field to url field.

Requirement:
1. Apache Web Server
2. Set http://yourhost/images/ for Default URL
3. Set /var/www/images/ for Default File store
4. Schedule "object: ineco.ir.attachment, function: schedule_attachment "

""",
    'author': 'INECO',
    'depends': ["base","ineco_base"],
    'website': 'http://openerp.tititab.com',
    'update_xml': [
        'attachment_data.xml',
        'attachment_view.xml'
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
