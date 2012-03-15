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

class account_invoice(osv.osv):
    
    _name="account.invoice"
    _inherit="account.invoice"
    _columns={
        'receipt_id':fields.char('Receipt ID', size=32),
        'receipt_date':fields.date("Receipt Date"),
    }

    def create_receipt(self, cr, uid, ids, context=None):
        invoice = self.pool.get('account.invoice').browse(cr, uid, ids)[0]
        if invoice and invoice.receipt_id == False:
            receipt_no = self.pool.get('ir.sequence').get(cr, uid, 'ineco.account.tax.receipt.type')
            invoice.write({'receipt_date':time.strftime('%Y-%m-%d'), 'receipt_id': receipt_no})
        return True

account_invoice()