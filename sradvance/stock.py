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
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from osv import fields, osv
from tools.translate import _
import netsvc
import tools
import decimal_precision as dp
import logging

class stock_inventory_line(osv.osv):

    def _get_width_product(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.product_id.product_width
        return res

    def _get_length_product(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.product_id.product_length
        return res

    _name = "stock.inventory.line"
    _inherit = "stock.inventory.line"
    _description = "Extended for Inventory Line"
    _columns = {
        'product_width': fields.function(_get_width_product, method=True, string='Width', digits_compute= dp.get_precision('Sale Price')),
        'product_length': fields.function(_get_length_product, method=True, string='Length', digits_compute= dp.get_precision('Sale Price')),
    }
stock_inventory_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
