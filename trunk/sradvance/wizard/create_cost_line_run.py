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

import wizard
from osv import osv
import pooler
from osv import fields
import time

def _launch_wizard(self, cr, uid, data, context=None):
    pool = pooler.get_pool(cr.dbname)
    line_data = pool.get('sale.order.line').browse(cr, uid, data['id'],context=context)
    #print line_data.id
    if line_data:
        pool.get('sale.order.line').write(cr, uid, [data['id']],{'price_unit':1})
        cr.execute( ("delete from sale_order_line_addtionalcost where order_line_id = %d " % line_data.id) )
        bom_ids = pool.get('mrp.bom').search(cr, uid, [('product_id','=',line_data.product_id.id),('type','=','phantom')])
        bom = pool.get('mrp.bom').browse(cr, uid, bom_ids[0])    
        if bom:
            for line in bom.bom_lines:
                ft2 = 1
                m2 = 1
                if line_data.sr_width and line_data.sr_length:
                    ft2 = (line_data.sr_width * line_data.sr_length) / (304.8 * 304.8)
                    m2 = (line_data.sr_width * 2 / 1000) + (line_data.sr_length * 2 / 1000)
                if line.double_qty:
                    new_qty = '%.2f' % (line.product_qty * 2) or 1.0
                else:
                    new_qty = '%.2f' % line.product_qty or 1.0
                if line.product_id.product_use_ft2:
                    if line.double_qty:
                        new_qty = '%.2f' % (ft2 * 2) 
                    else:
                        new_qty = '%.2f' % ft2
                if line.product_id.product_use_m2:
                    if line.double_qty:
                        new_qty = '%.3f' % (m2 * 2)
                    else:
                        new_qty = '%.3f' % m2
                product_name = pool.get('product.product').name_get(cr, uid, [line.product_id.id], context=context)[0][1]
                cost_line_id = pool.get('sale.order.line.addtionalcost').create(cr, uid, {
                    'order_line_id':data['id'],
                    'product_id':line.product_id.id,
                    'product_qty': new_qty,
                    'price_unit': line.product_id.lst_price,
                    'product_uom':line.product_uom.id,
                    'name': product_name } )                
    return {}

class launch_map(wizard.interface):

    states= {'init' : {'actions': [],
                       'result':{'type':'action',
                                 'action': _launch_wizard,
                                 'state':'end'}
                       }
             }

launch_map('create_cost_line_run')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

