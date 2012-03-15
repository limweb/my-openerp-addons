# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
import netsvc
import asset

import sale
import sale_period

import decimal_precision as dp

from osv import fields,osv
from tools.translate import _

class procurement_order(osv.osv):
       
    def _get_period_name(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.move_id and line.move_id.picking_id :
                res[line.id] = line.move_id.picking_id.period_id.name
        return res

    def _get_product_name(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.move_id and line.move_id.picking_id :
                res[line.id] = line.move_id.picking_id.customer_product_id.name
        return res

    def _get_location_dest_name(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.move_id and line.move_id.picking_id :
                res[line.id] = line.move_id.location_dest_id.name
        return res
       
    _name = "procurement.order"
    _inherit = "procurement.order"
    _description = "Procurement of OMG Holding (Thailand) Co.,Ltd."#

    _columns = {
        'period_name': fields.function(_get_period_name, method=True, type="char", string='Period'),
        'customer_product_name': fields.function(_get_product_name, method=True, type="char", string='Customer Product'),
        'location_dest_name': fields.function(_get_location_dest_name, method=True, type="char", string='Destination'),
        'period_id': fields.many2one('omg.sale.period', 'Period'),
        'customer_product_id': fields.many2one('product.product', 'Customer Product', ondelete="restrict" ),
    }

    _defaults = {
        
    }    
        
procurement_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
