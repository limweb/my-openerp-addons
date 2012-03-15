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

from osv import osv, fields
import decimal_precision as dp

import math
import re
from tools.translate import _

class product_product(osv.osv):
    
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
    }
    
    _defaults = {
        'audit': False,
        'equipment': False,
    }
    
product_product()

class product_category(osv.osv):
    _name = 'product.category'
    _inherit = 'product.category'
    _description = "Insert Dummy Category"
    _columns = {
        'dummy_id': fields.many2one('product.category', 'Dummy Category'),
        'service_category': fields.boolean('As Service Category'),
    }
    _defaults = {
        'service_category': False
    }
product_category()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
