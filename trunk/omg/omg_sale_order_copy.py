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


from osv import fields, osv
from tools.translate import _
import decimal_precision as dp
import time
import netsvc
import pooler
from osv.orm import browse_record, browse_null

class omg_sale_order_copy(osv.osv_memory):
    
    _name = "omg.sale.order.copy"
    _description = "Copy Sale Order"
    _columns = {
        'order_id': fields.many2one('sale.order', 'Order Reference', required=True ),    
        }
    _defaults = {
    }
    def copy_sale_order(self, cr, uid, data, context=None): 
        cp_order_id = self.browse(cr,uid,data[0],context=context).order_id.id
        if cp_order_id:
            cp_order_line_ids = self.pool.get('sale.order.line').search(cr,uid,[('order_id','=',cp_order_id),('price_unit','=',0)])
            cp_order_line_obj = self.pool.get('sale.order.line').browse(cr,uid,cp_order_line_ids)        
        order_id = context and context.get('active_ids', False)
        if order_id:
            for line in cp_order_line_obj:
                check_service = self.pool.get('product.product').browse(cr,uid,line.product_id.id)
                if check_service.type != 'service':
                    order_obj = self.pool.get('sale.order.line').create(cr, uid, {
                        'order_id': order_id[0],
                        'name':line.name,
                        'product_id':line.product_id.id,
                        'product_uom':line.product_uom.id,
                        'with_branch':line.with_branch,
                        'with_period':line.with_period,
                        'apply_all_store':line.apply_all_store,
                        'omg_ratio':line.omg_ratio,
                        'omg_sampling':line.omg_sampling,
                        'product_uom_qty':line.product_uom_qty,
                        })            
            
        return {'type': 'ir.actions.act_window_close'}       

omg_sale_order_copy()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: