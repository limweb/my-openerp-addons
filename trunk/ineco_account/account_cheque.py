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

import time
from lxml import etree

import netsvc
from osv import osv, fields
import decimal_precision as dp
from tools.translate import _

class ineco_account_cheque_in(osv.osv):
    _name = "ineco.account.cheque.in"
    _description = "Ineco Account Cheque Receive Module"
    
    _columns = {
        'name': fields.char('Cheque No', size=32, required=True),
        'bank_id': fields.many2one('res.bank', 'Bank', ondelete='restrict', required=True),
        'branch': fields.char('Branch Name', size=100, required=True),
        'date_cheque':fields.date("Cheque Date"),
        'date_receive': fields.date("Receive Date"),
        'partner_id': fields.many2one('res.partner','Partner',ondelete='restrict'),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'active': fields.boolean('Active'),
        'state': fields.selection([('draft','Draft'), ('process','In Progress'),('reject','Reject'),('done','Done')], 'State', readonly=True),
    }
    
    _defaults = {
        'active': True,
        'state': 'draft',
    }
    
ineco_account_cheque_in()

class ineco_account_cheque_out(osv.osv):
    _name = "ineco.account.cheque.out"
    _description = "Ineco Account Cheque Pay Module"
    
    _columns = {
        'name': fields.char('Cheque No', size=32, required=True),
        'bank_id': fields.many2one('res.bank', 'Bank', ondelete='restrict', required=True),
        'branch': fields.char('Branch Name', size=100, required=True),
        'date_cheque':fields.date("Cheque Date"),
        'date_pay': fields.date("Pay Date"),
        'partner_id': fields.many2one('res.partner','Partner',ondelete='restrict'),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'active': fields.boolean('Active'),
        'state': fields.selection([('draft','Draft'), ('process','In Progress'),('reject','Reject'),('done','Done')], 'State', readonly=True),
    }
    
    _defaults = {
        'active': True,
        'state': 'draft',
    }
    
ineco_account_cheque_out()