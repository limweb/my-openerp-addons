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

from osv import osv, fields
import netsvc
import pooler
from tools.translate import _
import decimal_precision as dp
from osv.orm import browse_record, browse_null


class purchase_order(osv.osv):
    _name = "purchase.order"
    _inherit = "purchase.order"
    _defaults = {
        'name': lambda obj, cr, uid, context: '/'
        }

    def create(self, cr, user, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            company_id = vals.get('company_id')
            seq_obj = self.pool.get('ir.sequence')
            seq_ids = seq_obj.search(cr, user, [('code','=','purchase.order'),('company_id','=',company_id)])
            sequence_id = 0
            if seq_ids:                
                sequence_id = seq_obj.browse(cr, user, seq_ids)[0].id
            else:
                raise osv.except_osv(_('Error !'), _('Can not find Purchase Sequence for Company.'))                
            vals['name'] = self.pool.get('ir.sequence').get_companyid(cr, user, sequence_id)
        return super(purchase_order,self).create(cr, user, vals, context)

    def action_picking_create(self,cr, uid, ids, *args):
        picking_id = False
        for order in self.browse(cr, uid, ids):
            loc_id = order.partner_id.property_stock_supplier.id
            istate = 'none'
            if order.invoice_method=='picking':
                istate = '2binvoiced'
            seq_obj = self.pool.get('ir.sequence')
            seq_ids = seq_obj.search(cr, uid, [('code','=','stock.picking.in'),('company_id','=',order.company_id.id)])
            sequence_id = 0
            if seq_ids:                
                sequence_id = seq_obj.browse(cr, uid, seq_ids)[0].id
            else:
                raise osv.except_osv(_('Error !'), _('Can not find Purchase Sequence for Company.'))                
            pick_name = seq_obj.get_companyid(cr, uid, sequence_id)
            #pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.in')
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
            self.pool.get('stock.move').action_confirm(cr, uid, todo_moves)
            self.pool.get('stock.move').force_assign(cr, uid, todo_moves)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        return picking_id


purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

