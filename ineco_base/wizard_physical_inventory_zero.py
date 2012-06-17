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
# 04-04-2012       DAY-001    ERROR PACK

from osv import fields, osv
from tools.translate import _
import decimal_precision as dp

class ineco_physical_inventory_setquantity(osv.osv_memory):
    _name = "ineco.physical.inventory.setquantity"
    _description = "Split into"
    _columns = {
        'quantity': fields.float('Quantity',digits_compute=dp.get_precision('Product UOM')),
    }
    _defaults = {
        'quantity': lambda *x: 0,
    }

    def set_quantity(self, cr, uid, data, context=None):
        if context is None:
            context = {}

        inventory_id = context and context.get('active_ids', False)
        inventory_obj = self.pool.get('stock.inventory')
        quantity = self.browse(cr, uid, data[0], context=context).quantity or 0.0

        for inv in inventory_obj.browse(cr, uid, inventory_id, context=context):
            for line in inv.inventory_line_id:
                line.write({'product_qty':quantity})
            
        return {'type': 'ir.actions.act_window_close'}
    
ineco_physical_inventory_setquantity()

