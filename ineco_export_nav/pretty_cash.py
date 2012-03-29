# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

# Date             ID         Message
# 21-12-2011       POP-001    Change file type to cp874 (support window)

import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp

import netsvc
import csv
import time
import codecs

from datetime import datetime
from operator import itemgetter

class ineco_nav_prettycash(osv.osv):
    _name = "ineco.nav.prettycash"
    _description = "Pretty Cash Export" 
    
    _columns = {
        'account_id': fields.many2one('account.account','Account No', required=True),
        'date_posting': fields.date('Posting Date', required=True),
        'reference_no': fields.char('Document No', size=20, required=True),
        'description': fields.char('Description', size=50),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account'), required=True),
        'date_reference': fields.date('Document Date'),
        'vat_bus_posting_group_id': fields.many2one('ineco.nav.postmaster', 'VAT Posting Group'),
        'invoice_no': fields.char('Invoice No', size=20, required=True),
        'date_invoice': fields.date('Invoice Date', required=True),
        'other_no': fields.char('Other No', size=20),
        'nav_exported': fields.boolean('Exported')
    }
    
    _defaults = {
        'nav_exported': False
    }

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        vals.update({'nav_exported': False})
        return super(ineco_nav_prettycash, self).write(cr, uid, ids, vals, context=context)
    
    def schedule_export_prettycash(self, cr, uid, context=None):
        pretty_ids = self.pool.get('ineco.nav.prettycash').search(cr, uid, [('nav_exported','=',False)])
        self.export_nav(cr, uid, pretty_ids, context)
        return True
        
    def export_nav(self, cr, uid, ids, context={}):
        for pretty in self.pool.get('ineco.nav.prettycash').browse(cr, uid, ids):
            config_ids = self.pool.get('ineco.export.config').search(cr, uid, [('type','=','pretty')])
            config_obj = self.pool.get('ineco.export.config').browse(cr, uid, config_ids)
            if config_obj:
                config = config_obj[0]
                path = False
                path = config.path+"PT"+('%.4d' % pretty.id)+".csv"
                #path = config.path+"pretty-"+str(pretty.id)+".csv"
                #POP-001
                f = open(path, 'wt')
                #f = codecs.open(path, encoding='cp874', mode='w+')
                writer = csv.writer(f)
                writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerow([
                    "PC",
                    pretty.account_id.code or "",
                    datetime.strptime(pretty.date_posting, '%Y-%m-%d').strftime('%d/%m/%Y'),
                    pretty.reference_no.encode('cp874') or "",
                    pretty.description.encode('cp874') or "",
                    pretty.amount,
                    datetime.strptime(pretty.date_reference, '%Y-%m-%d').strftime('%d/%m/%Y'),
                    pretty.vat_bus_posting_group_id.code_nav or "", #NAV Vat. Product Posting Group (Change New)
                    pretty.invoice_no.encode('cp874') or "",
                    datetime.strptime(pretty.date_invoice, '%Y-%m-%d').strftime('%d/%m/%Y'),
                    'ADV EMP',
                    pretty.other_no.encode('cp874') or "", #Personal ID 13 Digits
                    pretty.vat_bus_posting_group_id.code_nav or ""
                ])
                cr.execute("update ineco_nav_prettycash set nav_exported = True where id = %s " % pretty.id)
    
ineco_nav_prettycash()