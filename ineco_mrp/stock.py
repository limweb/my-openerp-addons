# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 INECO LTD, PARTNERSHIP (<http://www.ineco.co.th>).
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
# 21-06-2012       POP-001    Initialization

import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp
import netsvc

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from operator import itemgetter
from itertools import groupby

class stock_picking(osv.osv):
    _name = 'stock.picking'
    _inherit = 'stock.picking'
    _description = 'Add Production Order ID'
    _columns = {
        'production_id': fields.many2one('mrp.production','Manufacturing Order',ondelete="cascade")
    }
    
stock_picking()

class stock_production_lot(osv.osv):

    _inherit = 'stock.production.lot'
    _description = 'Add Default Ref in Production lot'

#    def create(self, cr, user, vals, context=None):
#        if ('product_id' in vals) :
#            product = self.pool.get('product.product').browse(cr, user, [vals['product_id']])[0]
#            vals['ref'] = product.default_code or vals['product_id']
#        new_id = super(stock_production_lot, self).create(cr, user, vals, context)
#        return new_id
    
    _sql_constraints = [
        ('name_product_uniq', 'unique (name, product_id)', 'The combination of Serial and Product must be unique !'),
    ]

stock_production_lot()