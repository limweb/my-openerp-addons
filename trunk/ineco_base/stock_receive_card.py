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

#
# 17-01-2012    POP-001    Change no-duplicate load pack
# 17-01-2012    POP-002    Change load packing card not in cancel state.
# 18-01-2012    POP-003    Change sure pack no available in load packing no.
# 09-05-2012    POP-004    Add Default Category ID

from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import time


class stock_receive_card(osv.osv_memory):
    
    _name = "ineco.stock.receive.card"
    _description = "Load Receive Card"
    _columns = {
        'location_dest_id': fields.many2one('stock.location', 'Destination Location', required=True ),
        'tracking_id': fields.many2one('stock.tracking','Pack No', required=True),
    }
    _defaults = {
    }

    def load(self, cr, uid, data, context=None):
        location_dest_id = self.browse(cr, uid, data[0], context=context).location_dest_id 
        tracking_id = self.browse(cr, uid, data[0], context=context).tracking_id
        pick_id = context and context.get('active_ids', False)
        
        if pick_id:
            pick_obj = self.pool.get('stock.picking').browse(cr, uid, pick_id)[0]
            track_obj = self.pool.get('stock.tracking')
            stock_move_obj = self.pool.get('stock.move')
            for track in track_obj.browse(cr, uid, [tracking_id.id], context=context):
                #POP-003
                stock_ids = self.pool.get('ineco.stock.report').search(cr, uid, [('tracking_id','=',track.id),('qty','>',0)])
                if stock_ids:
                    stock_obj = self.pool.get('ineco.stock.report').browse(cr, uid, stock_ids)[0]
                    uom_obj = self.pool.get('product.uom').browse(cr, uid, [stock_obj.uom_id.id])
                    move_id = self.pool.get('stock.move').create(cr, uid, {
                        'name': stock_obj.product_id.name, # move.name,
                        'picking_id': pick_obj.id ,
                        'product_id': stock_obj.product_id.id, # move.product_id.id,
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'date_expected': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'product_qty': stock_obj.qty, # move.product_qty,
                        'product_uom': stock_obj.uom_id.id, # move.product_uom.id,
                        'product_uos_qty': stock_obj.qty, # move.product_uos_qty,
                        'product_uos': stock_obj.uom_id.id, # move.product_uos.id,
                        'tracking_id': track.id, # move.tracking_id.id,
                        'prodlot_id': stock_obj.lot_id.id, # move.prodlot_id.id,
                        'product_packaging': False, #move.product_packaging.id or False,
                        'address_id': False,
                        'location_id': stock_obj.location_dest_id.id, # move.location_dest_id.id,
                        'location_dest_id': location_dest_id.id,
                        'sale_line_id': False,
                        'state': 'assigned',
                        'note': 'load packing',
                        'company_id': pick_obj.company_id.id,# move.company_id.id,
                        #POP-004
                        'category_id': stock_obj.uom_id.category_id.id,
                    })
                else:
                    raise osv.except_osv(_('Error !'), _('Can not find available Pack No -> '+track.name))    
#                location_id = False
#                for move in track.move_ids:
#                    #POP-002
#                    if move.state <> 'cancel':
#                        if location_id == False:
#                            location_id = move.location_dest_id.id
#                        if location_id == move.location_dest_id.id:
#                            #POP-001         
#                            search_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','=',pick_obj.id),
#                                ('tracking_id','=',move.tracking_id.id),('prodlot_id','=',move.prodlot_id.id)])        
#                            if not search_ids:
#                                move_id = self.pool.get('stock.move').create(cr, uid, {
#                                    'name': move.name,
#                                    'picking_id': pick_obj.id ,
#                                    'product_id': move.product_id.id,
#                                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
#                                    'date_expected': time.strftime('%Y-%m-%d %H:%M:%S'),
#                                    'product_qty': move.product_qty,
#                                    'product_uom': move.product_uom.id,
#                                    'product_uos_qty': move.product_uos_qty,
#                                    'product_uos': move.product_uos.id,
#                                    'tracking_id': move.tracking_id.id,
#                                    'prodlot_id': move.prodlot_id.id,
#                                    'product_packaging': move.product_packaging.id or False,
#                                    'address_id': False,
#                                    'location_id': move.location_dest_id.id,
#                                    'location_dest_id': location_dest_id.id,
#                                    'sale_line_id': False,
#                                    'tracking_id': move.tracking_id.id,
#                                    'state': 'draft',
#                                    #'state': 'waiting',
#                                    'note': move.note,
#                                    'company_id': move.company_id.id,
#                                })
#                            else:
#                                raise osv.except_osv(_('Error !'), _('You can not load already this pack.'))
                            
            
        return {'type': 'ir.actions.act_window_close'}
    
stock_receive_card()

