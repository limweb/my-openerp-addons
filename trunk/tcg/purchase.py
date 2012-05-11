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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta


import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp
import netsvc


class purchase_order(osv.osv):
    _name = "purchase.order"
    _inherit = "purchase.order"
    _description = "Purchase for TCG"
    _columns = {
        'purchase_order_no': fields.char('Purchase Order No', size=64),
        'department_id': fields.many2one('hr.department','Department'),
    }

#    def create(self, cr, user, vals, context=None):
#        if ('department_id' not in vals):
#            user_obj = self.pool.get('res.users').browse(cr, user, user)
#            vals['department_id'] = user_obj.context_department_id.id or False
#        new_id = super(stock_picking, self).create(cr, user, vals, context)
#        return new_id

    def action_cancel(self, cr, uid, ids, context=None):
        for purchase in self.browse(cr, uid, ids, context=context):
            for pick in purchase.picking_ids:
                if pick.state not in ('draft','cancel'):
                    raise osv.except_osv(
                        _('Could not cancel purchase order !'),
                        _('You must first cancel all picking attached to this purchase order.'))
            for pick in purchase.picking_ids:
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
            for inv in purchase.invoice_ids:
                if inv and inv.state not in ('cancel','draft'):
                    raise osv.except_osv(
                        _('Could not cancel this purchase order !'),
                        _('You must first cancel all invoices attached to this purchase order.'))
                if inv:
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'account.invoice', inv.id, 'invoice_cancel', cr)
        self.write(cr,uid,ids,{'state':'cancel', 'purchase_order_no':False})
        for (id,name) in self.name_get(cr, uid, ids):
            message = _("Purchase order '%s' is cancelled.") % name
            self.log(cr, uid, id, message)
        return True

    def wkf_approve_order(self, cr, uid, ids, context=None):
        po_no = self.pool.get('ir.sequence').get(cr, uid, 'ineco.purchase.order.tcg')
        self.write(cr, uid, ids, {'state': 'approved', 'date_approve': time.strftime('%Y-%m-%d'),'purchase_order_no':po_no})
        return True
    
    def action_picking_create(self,cr, uid, ids, *args):
        picking_id = False
        #po_no = self.pool.get('ir.sequence').get(cr, uid, 'ineco.purchase.order.tcg')
        for order in self.browse(cr, uid, ids):
            loc_id = order.partner_id.property_stock_supplier.id
            istate = 'none'
            if order.invoice_method=='picking':
                istate = '2binvoiced'
            pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in')
            picking_id = self.pool.get('stock.picking').create(cr, uid, {
                'name': pick_name,
                'origin': order.name+((order.origin and (':'+order.origin)) or ''),
                'type': 'in',
                'address_id': order.dest_address_id.id or order.partner_address_id.id,
                'invoice_state': istate,
                'purchase_id': order.id,
                'company_id': order.company_id.id,
                'move_lines' : [],
            })
            todo_moves = []
            for order_line in order.order_line:
                if not order_line.product_id:
                    continue
                if order_line.product_id.product_tmpl_id.type in ('product', 'consu'):
                    dest = order.location_id.id
                    move = self.pool.get('stock.move').create(cr, uid, {
                        'name': order.name + ': ' +(order_line.name or ''),
                        'product_id': order_line.product_id.id,
                        'product_qty': order_line.product_qty,
                        'product_uos_qty': order_line.product_qty,
                        'product_uom': order_line.product_uom.id,
                        'product_uos': order_line.product_uom.id,
                        'date': order_line.date_planned,
                        'date_expected': order_line.date_planned,
                        'location_id': loc_id,
                        'location_dest_id': dest,
                        'picking_id': picking_id,
                        'move_dest_id': order_line.move_dest_id.id,
                        'state': 'draft',
                        'purchase_line_id': order_line.id,
                        'company_id': order.company_id.id,
                        'price_unit': order_line.price_unit
                    })
                    if order_line.move_dest_id:
                        self.pool.get('stock.move').write(cr, uid, [order_line.move_dest_id.id], {'location_id':order.location_id.id})
                    todo_moves.append(move)
            #order.write({'purchase_order_no': po_no})
            self.pool.get('stock.move').action_confirm(cr, uid, todo_moves)
            self.pool.get('stock.move').force_assign(cr, uid, todo_moves)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        return picking_id

purchase_order()