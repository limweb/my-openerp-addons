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

# 09-04-2012    POP-001    Initial

import netsvc
import time

from osv import osv,fields
from tools.translate import _

class stock_return_picking(osv.osv_memory):
    
    _name = 'stock.return.picking'
    _inherit = 'stock.return.picking'
    _description = 'Return Picking'
    _columns = {
     }
    
    def create_returns(self, cr, uid, ids, context=None):
        """ 
         Creates return picking.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: List of ids selected
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        if context is None:
            context = {} 
        record_id = context and context.get('active_id', False) or False
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        uom_obj = self.pool.get('product.uom')
        data_obj = self.pool.get('stock.return.picking.memory')
        wf_service = netsvc.LocalService("workflow")
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        data = self.read(cr, uid, ids[0], context=context)
        new_picking = None
        date_cur = time.strftime('%Y-%m-%d %H:%M:%S')
        set_invoice_state_to_none = True
        returned_lines = 0
        
#        Create new picking for returned products
        if pick.type=='out':
            new_type = 'in'
        elif pick.type=='in':
            new_type = 'out'
        else:
            new_type = 'internal'
        new_picking = pick_obj.copy(cr, uid, pick.id, {'name':'%s-return' % pick.name,
                'move_lines':[], 'state':'draft', 'type':new_type, 
                'date':date_cur, 'invoice_state':data['invoice_state'],
                #POP-001
                'ineco_return': True,
                'ineco_request_user_id': uid,
                  })
        
        val_id = data['product_return_moves']
        for v in val_id:
            data_get = data_obj.read(cr, uid, v)
            mov_id = data_get['move_id']
            new_qty = data_get['quantity']
            #change by pop
            move = move_obj.browse(cr, uid, mov_id[0], context=context)#DAY
            new_location=move.location_dest_id.id
            returned_qty = move.product_qty
            for rec in move.move_history_ids2:
                returned_qty -= rec.product_qty

            if returned_qty != new_qty:
                set_invoice_state_to_none = False
            if new_qty:
                returned_lines += 1
                new_move=move_obj.copy(cr, uid, move.id, {
                    'product_qty': new_qty,
                    'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id,
                        new_qty, move.product_uos.id),
                    'picking_id':new_picking, 'state':'draft',
                    'location_id':new_location, 'location_dest_id':move.location_id.id,
                    'date':date_cur,})
                move_obj.write(cr, uid, [move.id], {'move_history_ids2':[(4,new_move)]})
        if not returned_lines:
            raise osv.except_osv(_('Warning !'), _("Please specify at least one non-zero quantity!"))

        if set_invoice_state_to_none:
            pick_obj.write(cr, uid, [pick.id], {'invoice_state':'none'})
        wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
        pick_obj.force_assign(cr, uid, [new_picking], context)
        # Update view id in context, lp:702939
        view_list = {
                'out': 'view_picking_out_tree',
                'in': 'view_picking_in_tree',
                'internal': 'vpicktree',
            }
        data_obj = self.pool.get('ir.model.data')
        res = data_obj.get_object_reference(cr, uid, 'stock', view_list.get(new_type, 'vpicktree'))
        context.update({'view_id': res and res[1] or False})
        return {
            'domain': "[('id', 'in', ["+str(new_picking)+"])]",
            'name': 'Picking List',
            'view_type':'form',
            'view_mode':'tree,form',
            'res_model':'stock.picking',
            'type':'ir.actions.act_window',
            'context':context,
        }

stock_return_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

