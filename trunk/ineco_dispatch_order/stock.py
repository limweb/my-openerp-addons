# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

# 11-10-2012    POP-001    Initial

import socket
import sys

import time
import netsvc
import asset

import sale
import sale_period

import decimal_precision as dp

from osv import fields,osv
from tools.translate import _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

import re

import tools 

class ineco_dispatch_product_summary(osv.osv):
    _name = "ineco.dispatch.product.summary"
    _description = "Dispatch Product Summary"
    _columns = {
        'name': fields.char('Description', size=250),
        'product_id': fields.many2one('product.product','Product', required=True, select=True),
        'uom_id': fields.manh2one('product.uom','Default UoM', required=True),
        'total': fields.float('Total', digits_compute=dp.get_precision('Product UoM'), required=True),
        'dispatch_id': fields.many2one('ineco.dispatch.order','Dispatch Order'),        
    }
    _defaults = {
        'name': '',
        'total': 0.0,
    }
ineco_dispatch_product_summary()

class ineco_dispatch_order(osv.osv):
    _name = "ineco.dispatch.order"
    _description = "Dispatch Order"
    _columns = {
        'name': fields.char('Job No', size=30, required=True, select=True),
        'date': fields.date('Job Date', required=True, select=True),
        'date_confirm': fields.date('Date Confirm', select=True, ),
        'date_complete': fields.date('Date Complete', select=True, ),
        'order_ids': fields.many2many('sale.order', 'sale_order_dispatch_order_rel', 'child_id', 'parent_id', 'Sale Order'),
        'pick_ids': fields.one2many('stock.picking','Delivery Order'),
        'move_ids': fields.one2many('stock.move', 'Stock Move'),
        'summary_ids': fields.one2many('ineco.dispatch.product.summary','Product Summary'),
        'note': fields.text('Note'),
        'state': fields.selection([('draft','Draft'),('confirm','Confirm'),('done','Done'),('cancel','Cancel')], 'State', select=True),
    }
    _defaults = {
        'name': '/',
        'date': time.strftime('%Y-%m-%d'),        
        'state': 'draft',
    }
    
    def create(self, cr, uid, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            sequence_id = self.pool.get('ir.sequence').get(cr, uid, 'ineco.dispatch.order.type')
            if not sequence_id:                
                raise osv.except_osv(_('Error !'), _('Can not find Dispatch Order Sequence for Company.'))                
            vals['name'] = sequence_id
        return super(ineco_dispatch_order, self).create(cr, uid, vals, context=context)
 
    def act_confirm(self, cr, uid, ids, *args):
        for line in self.browse(cr, uid, ids):
            for do in line.order_ids:
                do.write({'dispatch_order_id': line.id })
        self.write(cr, uid, ids, {'state': 'confirm', 'date_confirm': time.strftime('%Y-%m-%d') })
        return True

    def act_done(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'done', 'date_complete': time.strftime('%Y-%m-%d')})
        return True

    def act_cancel(self, cr, uid, ids, *args):
        for line in self.browse(cr, uid, ids):
            for do in line.order_ids:
                do.write({'dispatch_order_id': False, 'date_complete': False })
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True

    def act_setdraft(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft', 'date_confirm': False, 'date_complete': False  })
        return True
    
ineco_dispatch_order()

class ineco_delivery_type(osv.osv):
    
    _name = "ineco.delivery.type"
    _description = "Delivery Type"
    
    _columns = {
        'name': fields.char('Delivery Type', size=50, required=True, select=True),
        'print_issue': fields.boolean('Print Issued'),
        'print_delivery_order': fields.boolean('Print Delivery Order'),
    }
    
    _defaults = {
        'print_issue': False,
        'print_delivery_order': False,
    }

    _sql_constraints = [
        ('delivery_type_name_unique', 'unique (name)', 'Name must be unique!')
    ]
    
ineco_delivery_type()

class stock_move(osv.osv):
    _inherit = "stock.move"
    _columns = {
        'ineco_delivery_type_id': fields.many2one('ineco.delivery.type', 'Delivery Type'),
    }
stock_move()
