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
    'name': 'SR Advance - Chart of Accounts',
    'version': '0.1',
    'category': 'Localisation/Account Charts',
    'description': """
Chart of accounts for SR Advance Co.,Ltd..
    """,
    'author': 'mr.tititabl.com (ineco)',
    'website': 'http://openerp.tititab.com/',
    'depends': ['account_chart'],
    'init_xml': [],
    'update_xml': [ 'account_data.xml' ],
    'installable': True,
}
