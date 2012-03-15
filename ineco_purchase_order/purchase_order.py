##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
import tools

from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import osv, fields
import netsvc
import pooler
from tools.translate import _
import decimal_precision as dp
from osv.orm import browse_record, browse_null

class purchase_order(osv.osv):
    _name = 'purchase.order'
    _inherit = 'purchase.order'
    _description = "Add payment term in purchase order"
    _columns = {
        'payment_id': fields.many2one('account.payment.term', 'Payment Term'),
    }
    
    def onchange_partner_id(self, cr, uid, ids, part):

        if not part:
            return {'value':{'partner_address_id': False, 'fiscal_position': False}}
        addr = self.pool.get('res.partner').address_get(cr, uid, [part], ['default'])
        part = self.pool.get('res.partner').browse(cr, uid, part)
        pricelist = part.property_product_pricelist_purchase.id
        fiscal_position = part.property_account_position and part.property_account_position.id or False
        payment_id = part.property_payment_term and part.property_payment_term.id or False
        return {'value':{'partner_address_id': addr['default'], 'pricelist_id': pricelist, 'fiscal_position': fiscal_position,'payment_id': payment_id}}
    
purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

