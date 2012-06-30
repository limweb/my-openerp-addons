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

#class product_product(osv.osv):
#    
#    _name = 'product.product'
#    _inherit = 'product.product'
#    _description = 'Add Stock Journal In Product.Product'
#    _columns = {
#        'ineco_stock_journal_id': fields.many2one('stock.journal','Stock Journal'),
#    }
    
#product_product()

class product_uom(osv.osv):
    
    _name = 'product.uom'
    _inherit = 'product.uom'
    _description = 'change uom warning'
    
    def _compute_qty_obj(self, cr, uid, from_unit, qty, to_unit, context=None):
        if context is None:
            context = {}
        if from_unit.category_id.id <> to_unit.category_id.id:
            #if context.get('raise-exception', True):
            #    raise osv.except_osv(_('Error !'), _('Conversion from Product UoM %s to Default UoM %s is not possible as they both belong to different Category!.') % (from_unit.name,to_unit.name,))
            #else:
            return qty
        amount = qty / from_unit.factor
        if to_unit:
            amount = rounding(amount * to_unit.factor, to_unit.rounding)
        return amount
    
product_uom()    