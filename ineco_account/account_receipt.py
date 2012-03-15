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

class ineco_account_receipt(osv.osv):
    
    def _get_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            voucher_total = 0
            for voucher in line.voucher_ids:
                voucher_total = voucher_total + voucher.amount
            res[line.id] = voucher_total
        return res
    
    _name = "ineco.account.receipt"
    _description = "Ineco Account Receipt Module"
    
    _columns = {
        'name':fields.char('Receipt ID', size=32, select=True, required=True),
        'receipt_date':fields.date("Receipt Date", select=True, required=True),
        'partner_id' : fields.many2one('res.partner', 'Customer', required=True, ondelete='restrict'),
        'address_id' : fields.many2one('res.partner.address','Invoice Address', required=True, ondelete="restrict"),
#        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account'),),
        'amount': fields.function(_get_amount, digits_compute=dp.get_precision('Account'), method=True, type='float', string='Amount'),
        'voucher_ids': fields.one2many('ineco.account.receipt.line','receipt_id','Billing Notes'),
        'journal_id':fields.many2one('account.journal', 'Journal', required=True),
    }
    
    _order = "name desc"
    
    _defaults = {
        'name': lambda obj, cr, uid, context: '/'        
    }
    
    def create(self, cr, user, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            if ('journal_id' in vals):
                sequence_id = vals.get('journal_id') 
                seqobj = self.pool.get('account.journal').browse(cr, user, [sequence_id])[0]
                #seq_obj = self.pool.get('ir.sequence')
                #seq_ids = seq_obj.search(cr, user, [('code','=','ineco.account.receipt.type')])
                #sequence_id = 0
                #if seq_ids:                
                #    sequence_id = seq_obj.browse(cr, user, seq_ids)[0].id
                #else:
                #    raise osv.except_osv(_('Error !'), _('Can not find Receipt for Company.'))  
                             
                vals['name'] = self.pool.get('ir.sequence').get_companyid(cr, user, seqobj.sequence_id.id)
        return super(ineco_account_receipt,self).create(cr, user, vals, context)

    def onchange_partner_id(self, cr, uid, ids, part):
        if not part:
            return {'value': {'address_id': False}}
        addr = self.pool.get('res.partner').address_get(cr, uid, [part], ['delivery', 'invoice', 'contact'])
        part = self.pool.get('res.partner').browse(cr, uid, part)
        val = {
            'address_id': addr['invoice'],
        }
        return {'value': val}
    
ineco_account_receipt()

class ineco_account_receipt_line(osv.osv):
    _name = "ineco.account.receipt.line"
    _description = "Ineco Account Receipt Module (Line)"
    
    _columns = {
        'name': fields.char('Description', size=255, required=True),
        'voucher_id': fields.many2one('account.voucher', 'Billing ID', ondelete='restrict'),
        'date_voucher':fields.date("Voucher Date", required=True),
        'date_due':fields.date("Date Due", required=True),        
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'receipt_id': fields.many2one('ineco.account.receipt', 'Receipt', ondelete='restrict'),        
    }
    
    def onchange_voucher(self, cr, uid, ids, voucher):
        if not voucher:
            return {'value': {'name': False, 'amount': False}}
        bill = self.pool.get('account.voucher').browse(cr, uid, [voucher], ['bill_number','amount_bill','date','appointment_date'])[0]
        val = {
            'name': bill.bill_number,
            'amount': bill.amount_bill,
            'date_voucher': bill.date,
            'date_due': bill.appointment_date,
        }
        return {'value': val}

ineco_account_receipt_line()