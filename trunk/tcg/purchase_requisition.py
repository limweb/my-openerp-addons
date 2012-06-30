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

from osv import fields,osv
import decimal_precision as dp
from tools.translate import _

class purchase_requisition(osv.osv):
    _name = "purchase.requisition"
    _inherit = "purchase.requisition"
    _description="Purchase Requisition"
    _columns = {
        'cash_only': fields.boolean('Cash'),
        'amount': fields.float('Amount', digits_compute= dp.get_precision('Account')),
    }
    _defaults = {
        'cash_only': False,
        'date_start': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    def create(self, cr, uid, vals, context=None):
        vals.update({'date_start': time.strftime('%Y-%m-%d %H:%M:%S')})
        return super(purchase_requisition, self).create(cr, uid, vals, context)

purchase_requisition()