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

from osv import fields, osv
import netsvc
import pooler
from osv.orm import browse_record, browse_null
from tools.translate import _

class update_location_qty_estimate(osv.osv_memory):
    
    _name = "update.location.qty.estimate"
    _description = "Update Location Qty"
    
    def update_location_qty(self, cr, uid, ids, context=None):
        if context is None:
            context = {}   
        update_qty = self.pool.get('stock.location.line.qty.update')         
        for location_qty_update in update_qty.browse(cr, uid, context['active_ids'], context=context):
            product_cate = self.pool.get('product.category').search(cr,uid,[('parent_id','=',location_qty_update.categ_id.id)])          
            location_qty_ids = self.pool.get('stock.location.line.qty').search(cr,uid,[('location_id','=',location_qty_update.location_id.id),('categ_id','in',product_cate)])
            if len(location_qty_ids) == 1:
                sql_update_qty = 'update stock_location_line_qty set quantity = %s where id in %s' %(location_qty_update.quantity,location_qty_ids)
                cr.execute(sql_update_qty)
                cr.commit()
            elif len(location_qty_ids) > 1:
                sql_update_qty = 'update stock_location_line_qty set quantity = %s where id in %s ' %(location_qty_update.quantity,tuple(location_qty_ids))
                cr.execute(sql_update_qty)
                cr.commit()    
                                    
        return {'type':'ir.actions.act_window_close' }    
    
update_location_qty_estimate()    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: