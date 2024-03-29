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

# 07-05-2012     POP-001    Add Use Full Warehouse UOM
# 29-05-2012     DAY-001    Add product_category_retailer
# 20-07-2012     POP-002    Add Not Print Delivery Order
# 14-08-2012     DAY-002    Add sql_constraints ean13
# 21-08-2012     DAY-003    Add Field Name2

from osv import osv, fields
import decimal_precision as dp

import math
import re
from tools.translate import _

class product_product(osv.osv):

    def _get_name_lock(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid)
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = user.read_only_product_name
        return res
    
    _name = "product.product"
    _inherit = "product.product"
    _description = "Product extended for Product"
    _columns = {
        'use_location_qty':fields.boolean("Use Location Qty"),
        'customer_product':fields.boolean("Customer Product"),
        'service_type': fields.boolean('As Service Type'),
        'audit': fields.boolean('Audit Service'),
        'customer_material': fields.boolean("Customer Material"),
        'cash_advance': fields.boolean("Cash Advance"),
        'equipment': fields.boolean('Equipment'),
        'item_sale_check_ids': fields.many2many('product.product', 'sale_order_product_product_rel', 'child_id', 'product_tmpl_id', 'Item Check Sales'),
        'name_lock': fields.function(_get_name_lock, method=True, type='boolean', string="Lock By PM"),
        #POP-001
        'full_warehouse_uom': fields.boolean('Full Warehouse Uom'),
        #POP-002
        'not_print_do': fields.boolean("Not Print Delivery Order"),
        #DAY-003
        'name2': fields.char('Name2', size=128),

    }
    
    _defaults = {
        'audit': False,
        'equipment': False,
        'full_warehouse_uom': False,
    }
    #POP-002
    _sql_constraints = [
        ('ean13_unique', 'unique (ean13)', "ข้อมูล EAN13 ซ้ำ")
    ]
    
product_product()

class product_category(osv.osv):
    _name = 'product.category'
    _inherit = 'product.category'
    _description = "Insert Dummy Category"
    _columns = {
        'dummy_id': fields.many2one('product.category', 'Dummy Category'),
        'service_category': fields.boolean('As Service Category'),
        'ineco_check_place': fields.boolean('Check Place'),
        'ineco_check_categ': fields.boolean('Check Category'),
        'retailer_categ_ids': fields.one2many('product.category.retailer', 'categ_id', 'Retailer Name'),
         
    }
    _defaults = {
        'service_category': False,
        'ineco_check_place': False,
        'ineco_check_categ': False,
    }
product_category()

class product_category_retailer(osv.osv):
    _name = 'product.category.retailer'
    _description = 'Category by Chain'
    _columns = {'name':fields.char('Retailer Name', size=64, select=True, required=True),
                'chain_id': fields.many2one('omg.sale.chain', 'Chain', ondelete="restrict",required=True),
                'categ_id': fields.many2one('product.category','Category',required=True, ondelete='restrict'),
                }

product_category_retailer()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
