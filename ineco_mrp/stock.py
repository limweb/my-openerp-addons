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

    #Change Sequence in Stock Production Lot to %(year)s%(month)s%(day)s and step = 0
    def create(self, cr, uid, vals, context=None):
        product_obj = self.pool.get('product.product').browse(cr, uid, vals['product_id'])
        lot_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.lot.serial')
        lot_ids =  self.pool.get('stock.production.lot').search(cr, uid, [('product_id','=',product_obj.id),('name','=',lot_name)]) 
        vals.update({'prefix': product_obj.default_code,'ref': len(lot_ids) + 1 })
        return super(stock_production_lot, self).create(cr, uid, vals, context)

#    def create(self, cr, user, vals, context=None):
#        if ('product_id' in vals) :
#            product = self.pool.get('product.product').browse(cr, user, [vals['product_id']])[0]
#            vals['ref'] = product.default_code or vals['product_id']
#        new_id = super(stock_production_lot, self).create(cr, user, vals, context)
#        return new_id
    
    _sql_constraints = [
        ('name_product_ref_uniq', 'unique (name, product_id, ref)', 'The combination of Serial, Ref and Product must be unique !'),
    ]

stock_production_lot()