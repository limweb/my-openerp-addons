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

class account_voucher(osv.osv):
    _name="account.voucher"
    _inherit="account.voucher"
    _columns={
        'type':fields.selection([
            ('sale','Sale'),
            ('purchase','Purchase'),
            ('payment','Payment'),
            ('receipt','Receipt'),
            ('bill','Billing Note'),],'Default Type', readonly=True, states={'draft':[('readonly',False)]}),
        'bill_number': fields.char('Billing Number', size=20, readonly=True), 
        'appointment_date':fields.date('Appointment Date'),
        'state':fields.selection(
            [('draft','Draft'),
             ('proforma','Pro-forma'),
             ('posted','Posted'),
             ('cancel','Cancelled'),
             ('billed','Billed'),
            ], 'State', readonly=True, size=32,
            help=' * The \'Draft\' state is used when a user is encoding a new and unconfirmed Voucher. \
                        \n* The \'Pro-forma\' when voucher is in Pro-forma state,voucher does not have an voucher number. \
                        \n* The \'Posted\' state is used when user create voucher,a voucher number is generated and voucher entries are created in account \
                        \n* The \'Cancelled\' state is used when user cancel voucher.'),
        'amount_bill':fields.float('Billing Amount', digits_compute=dp.get_precision('Account'), readonly=True),
        'receipt_id': fields.many2one('ineco.account.receipt', 'Receipt', ondelete='restrict'),
    }
    
    _defaults = {
        
    }
    
    def create_billing(self, cr, uid, ids, context=None):
        billno = self.pool.get('ir.sequence').get(cr, uid, 'ineco.account.tax.receipt.type')
        voucher = self.pool.get('account.voucher').browse(cr, uid, ids)[0]
        credit = 0
        debit = 0
        for cr in voucher.line_cr_ids:
            if cr.amount_unreconciled:
                credit = credit + cr.amount_unreconciled
        for dr in voucher.line_dr_ids:
            if dr.amount:
                debit = debit + dr.amount
        balance = credit- debit 
        voucher.write({'amount_bill':balance,'state':'billed','bill_number': billno})
        return True

account_voucher()