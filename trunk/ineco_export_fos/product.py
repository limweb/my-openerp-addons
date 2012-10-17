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

# 17-10-2012    POP-001    Change size of FOS Code from 20 to 100

from datetime import datetime
from osv import osv, fields
from tools.translate import _
import netsvc
import time
import tools
import decimal_precision as dp

class product_product(osv.osv):
    
    _name = 'product.product'
    _inherit = 'product.product'
    _description = 'Add Fos Code In Product.Product'
    _columns = {
        'ineco_fos_code': fields.char('FOS Code', size=100),
        'check_link': fields.boolean('Check Link'),
    }
    
    _defaults = {
        'check_link': False,
    }
    
product_product()