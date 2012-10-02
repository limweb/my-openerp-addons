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


class omg_sale_order_cancel_type(osv.osv):
    
    _name ="omg.sale.order.cancel.type"
    _description ="Type Cancel Sale Order"
    _columns = {
            'name' : fields.char('Cancel Sale Order Type', size=64,required=True),
            'active': fields.boolean('Active'),            
    }
    _defaults = {
        'active': True,
    }  
    _sql_constraints = [
        ('omg_sale_order_cancel_type_unique','unique (name)', 'Type Cancel Sale Order must me unique.')
    ]
    
omg_sale_order_cancel_type()

class omg_sale_order_cancel_wizard(osv.osv_memory):
    _name = "omg.sale.order.cancel.wizard"
    _description = "Cancel Sale Order"
    _columns = {  
            'sale_id': fields.many2one('sale.order','Sale Order' ),
            'sale_cancel_ids': fields.many2many('omg.sale.order.cancel.type', 'sale_order_type_rel', 'sale_cancel_id', 'product_tmpl_id', 'Sale Order Type'),
            'note': fields.text('Notes',required=True),      
    }      
    def cancel_sale_order(self, cr, uid,data, context=None):     
        order_id = context and context.get('active_ids', False)
        if order_id:        
            sale_id = order_id
            for sale_line in self.pool.get('sale.order').browse(cr,uid,order_id):
                sale_order_name = sale_line.name       
        for check_type_ids in self.browse(cr, uid ,data, context=context):
            if check_type_ids:
                if check_type_ids.sale_cancel_ids:                
                    cr.execute('''select sequence from omg_sale_order_cancel where sale_id = %s order by sequence desc limit 1 ''' % sale_id[0])
                    seq = cr.dictfetchone()  
                    if seq:
                        seq = int(seq['sequence']) + 1                           
                    else:
                        seq = 1
                    for sale_cancel_line in check_type_ids.sale_cancel_ids:                    
                        self.pool.get('omg.sale.order.cancel').create(cr, uid, {
                                    'sale_id': sale_id[0],
                                    'name': sale_order_name,
                                    'sale_cancel_type_ids':sale_cancel_line.id,
                                    'note':check_type_ids.note,
                                    'sequence':seq,
                                })
                    self.pool.get('sale.order').action_cancel(cr, uid, order_id, context=context)    
                else:
                    raise osv.except_osv(_('Warning'), _("คุณยังไม่ได้ใส่เหตุผลการยกเลิกครับ.."))   
            else:
                raise osv.except_osv(_('Warning'), _("คุณยังไม่ได้ใส่เหตุผลการยกเลิกครับ.."))
             
                
        return {'type': 'ir.actions.act_window_close'}    
    
omg_sale_order_cancel_wizard()

class omg_sale_order_cancel(osv.osv):
    _name = "omg.sale.order.cancel"
    _description = "Cancel Sale Order"
    _columns = {  
            'name': fields.char('Order Reference', size=64,required=True),
            'sale_id': fields.many2one('sale.order','Sale Order'),
            'sale_cancel_type_ids': fields.many2one('omg.sale.order.cancel.type','Cancel Type'),
            'note': fields.text('Notes'),      
            'sequence':fields.integer('Sequence'),
            'user_cancel_id': fields.many2one('res.users', 'User Cancle' , ondelete="restrict"),
            'cancel_date': fields.datetime('Cancel Order Date'),          
    }  
    _defaults = {
        'cancel_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'user_cancel_id': lambda obj, cr, uid, context: uid,
    }
    
omg_sale_order_cancel()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: