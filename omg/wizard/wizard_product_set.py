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
from datetime import datetime
from dateutil.relativedelta import relativedelta

import decimal_precision as dp

from osv import fields, osv
from osv.orm import browse_record, browse_null
from tools.translate import _

class product_set_wizard(osv.osv_memory):
    _name = "sale.product.set.wizard"
    _description = "Browse Product Set"
    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True),
    }
                
product_set_wizard()




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
