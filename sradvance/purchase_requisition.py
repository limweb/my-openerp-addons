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
from tools.translate import _

class purchase_requisition(osv.osv):
    _name = "purchase.requisition"
    _inherit = "purchase.requisition"

    _description="Purchase Requisition"

    def create(self, cr, uid, vals, context=None):
        vals.update({'date_start': time.strftime('%Y-%m-%d %H:%M:%S')})
        return super(purchase_requisition, self).create(cr, uid, vals, context)

purchase_requisition()

class purchase_requisition_line(osv.osv):

    _name = "purchase.requisition.line"
    _inherit = "purchase.requisition.line"
    _description="Purchase Requisition Line insert uom category"

    _columns = {
        'uom_category_id': fields.many2one('product.uom.categ', 'UOM Category', ondelete="restrict"),
    }

    def onchange_product_id(self, cr, uid, ids, product_id,product_uom_id, context=None):
        """ Changes UoM and name if product_id changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        #value = {'product_uom_id': ''}
        value = {}
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            value = {'product_uom_id': prod.uom_id.id,'product_qty':1.0,'uom_category_id': prod.uom_id.category_id.id}
        return {'value': value}

purchase_requisition_line()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
