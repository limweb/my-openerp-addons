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

# Date             ID         Message
# 07-07-2012       POP-001    Initialization

from osv import fields, osv
from tools.translate import _
import decimal_precision as dp

import time
from datetime import datetime

class ineco_stock_clearing(osv.osv_memory):
    
    _name = "ineco.stock.clearing"
    _description = "Clearing Stock"
    
    _columns = {
        'quantity': fields.float('Quantity',digits_compute=dp.get_precision('Product UOM')),
        'product_id': fields.many2one('product.product','Product'),
        'uom_id': fields.many2one('product.uom','UOM'),
        'category_id': fields.many2one('product.uom.categ','Category'),
    }
    
    _defaults = {
        'quantity': 0,
    }

    def default_get(self, cr, uid, fields, context=None):
        """ To get default values for the object.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for which we want default values
        @param context: A standard dictionary
        @return: A dictionary which of fields with values.
        """
        if context is None:
            context = {}
        record_obj = self.pool.get('ineco.stock.report')
        res = super(ineco_stock_clearing, self).default_get(cr, uid, fields, context=context)
        data_obj = record_obj.browse(cr, uid, context.get('active_id', []))
        if data_obj:
            res['product_id'] = data_obj.product_id.id
            res['quantity'] = data_obj.qty
            res['uom_id'] = data_obj.uom_id.id
            res['category_id'] = data_obj.uom_id.category_id.id
        return res

#    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
#        result = super(ineco_stock_clearing, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
#        record_id = context and context.get('active_id', False) or False
#        product_data = {}
#        product_data['context'] = {}
#        product_data['domain'] = []
#        product_data['relation'] = 'product.product'
#        product_data['selectable'] = True
#        product_data['string'] = 'Product'
#        product_data['type'] = 'many2one'
#        product_data['views'] = {}
        

#        if (context.get('active_model') == 'ineco.stock.report') and record_id:
#            record_obj = self.pool.get('ineco.stock.report').browse(cr, uid, [record_id], context=context)[0]
#            fields = result.get('fields', {})
#           
#            if fields and fields.get('product_id'):
#                result['fields']['product_id'] = product_data

#        return result
        
    def execute(self, cr, uid, data, context=None):
        if context is None:
            context = {}
        uom_obj = self.pool.get('product.uom')
        quantity = self.browse(cr, uid, data[0], context=context).quantity
        product_id = self.browse(cr, uid, data[0], context=context).product_id
        default_uom = product_id.uom_id
        uom_id = self.browse(cr, uid, data[0], context=context).uom_id
        quantity = uom_obj._compute_qty_obj(cr, uid, uom_id, quantity, default_uom)
        amount = 0
        stock_report = self.pool.get('ineco.stock.report').browse(cr, uid, context.get('active_ids', []))[0]
        if stock_report:
            amount = stock_report.qty                    

        change = quantity - amount
        lot_id = False
        if stock_report.lot_id:                
            lot_id = stock_report.lot_id.id
        tracking_id = False
        if stock_report.tracking_id:
            tracking_id = stock_report.tracking_id.id
        if change:
            product_template = self.pool.get('product.template').browse(cr ,uid, [product_id.id] )[0]
            location_id = product_template.property_stock_inventory.id

            value = {
                'name': 'INV:Adjust Stock',
                'product_id': product_id.id,
                'product_uom': default_uom.id,
                'prodlot_id': lot_id,
                'tracking_id': tracking_id,
                'date': time.strftime('%Y-%m-%d'),
            }
            if change > 0:
                value.update( {
                    'product_qty': change,
                    'location_id': location_id,
                    'location_dest_id': stock_report.location_dest_id.id,
                })
            else:
                value.update( {
                    'product_qty': -change,
                    'location_id': stock_report.location_dest_id.id,
                    'location_dest_id': location_id,
                })
            stock_move = self.pool.get("stock.move")
            sm_id = stock_move.create(cr, uid, value)
            stock_move.write(cr, uid, sm_id, {'state':'done'})
            
        return {'type': 'ir.actions.act_window_close'}
    
ineco_stock_clearing()
