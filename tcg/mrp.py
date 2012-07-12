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

from datetime import datetime
from osv import osv, fields
from tools.translate import _
import netsvc
import time
import tools
import decimal_precision as dp

class mrp_bom(osv.osv):
    _name = "mrp.bom"
    _inherit = "mrp.bom"
    _description = "Change Product Qty Precision"
    _columns = {
        'product_qty': fields.float('Product Qty', required=True, digits_compute=dp.get_precision('Product UoM')),
    }
mrp_bom()

class mrp_production_product_line(osv.osv):
    _name = 'mrp.production.product.line'
    _inherit = 'mrp.production.product.line'
    _description = 'Production Scheduled Product'
    _columns = {
        'product_qty': fields.float('Product Qty', required=True, digits_compute=dp.get_precision('Product UoM')),
        'product_uos_qty': fields.float('Product UOS Qty', digits_compute=dp.get_precision('Product UoM')),
    }
mrp_production_product_line()