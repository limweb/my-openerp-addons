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
# 08-06-2012    POP-001    Change no-duplicate load pack
# 07-07-2012    POP-002    Add Before Qty

from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import time


class stock_inventory_load(osv.osv_memory):
    
    _name = "ineco.stock.inventory.card"
    _description = "Load Inventory Card"
    _columns = {
        'tracking_id': fields.many2one('stock.tracking','Pack No', required=True),
    }
    _defaults = {
    }

    def load(self, cr, uid, data, context=None):
        tracking_id = self.browse(cr, uid, data[0], context=context).tracking_id  
        inventory_id = context and context.get('active_ids', False)  
        if inventory_id:
            inventory_obj = self.pool.get('stock.inventory').browse(cr, uid, inventory_id)[0]
            track_obj = tracking_id
            stock_report_ids = self.pool.get('ineco.stock.report').search(cr, uid,
                [('qty','!=',0),('tracking_id','=',track_obj.id)])
            if stock_report_ids:
                stock_report_obj = self.pool.get('ineco.stock.report').browse(cr, uid, stock_report_ids)[0]                
                line_obj = self.pool.get('stock.inventory.line').create(cr, uid, {
                    'tracking_id': track_obj.id,
                    'inventory_id': inventory_obj.id,
                    'product_id': stock_report_obj.product_id.id ,
                    'product_uom': stock_report_obj.uom_id.id,
                    'prod_lot_id': stock_report_obj.lot_id.id,
                    'product_qty': stock_report_obj.qty,
                    'location_id': stock_report_obj.location_dest_id.id,
                    #POP-002
                    'before_qty': stock_report_obj.qty,
                })            
            else:
                raise osv.except_osv(_('Error !'), _('Can not find data.'))
        return {'type': 'ir.actions.act_window_close'}
    
stock_inventory_load()

