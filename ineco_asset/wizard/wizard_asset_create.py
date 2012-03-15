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

class stock_move_create_asset(osv.osv_memory):
    _name = "stock.move.asset.create"
    _description = "Create Barcode from Receiving"
    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'quantity': fields.integer('Quantity'),
        'register_date':fields.datetime("Register Date", select=True, required=True),
        'partner_id' : fields.many2one('res.partner', 'Partner', required=True),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Sale Price')),
        'company_id': fields.many2one('res.company', 'Company'),
        'notes':fields.text("Notes"),
    }
    

    def default_get(self, cr, uid, fields, context=None):
        """ Get default values
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for default value
        @param context: A standard dictionary
        @return: Default values of fields
        """
        if context is None:
            context = {}

        res = super(stock_move_create_asset, self).default_get(cr, uid, fields, context=context)
        if context.get('active_id'):
            move = self.pool.get('stock.move').browse(cr, uid, context['active_id'], context=context)
            if 'product_id' in fields:
                res.update({'product_id': move.product_id.id})
            if 'quantity' in fields:
                res.update({'quantity': move.product_qty})
            if 'register_date' in fields:
                res.update({'register_date': move.date})
            if 'partner_id' in fields:
                res.update({'partner_id': move.partner_id.id})
            if 'company_id' in fields:
                res.update({'company_id': move.company_id.id})
            if 'price_unit' in fields:
                res.update({'price_unit': move.price_unit})
            if 'notes' in fields:
                res.update({'notes': move.name})

        return res
    
    def create_asset(self, cr, uid, ids, context=None):
        if context is None :
            context = {}
        if context.get('active_id'):
            move = self.pool.get('stock.move').browse(cr, uid, context['active_id'], context=context)            
            if move.state == 'done':
                if move.ineco_asset_register == False:
                    asset_create_obj = self.browse(cr, uid, ids, context)[0]
                    asset_obj = self.pool.get('ineco.asset')          
                    for i in range(asset_create_obj.quantity):
                        asset_code = asset_create_obj.product_id.asset_seq_no.code
                        asset_seq_def = self.pool.get('ir.sequence').get(cr, uid, 'ineco.asset.type') 
                        asset_seq_get = self.pool.get('ir.sequence').get(cr, uid, asset_code) 
                        asect_seq = asset_seq_get or asset_seq_def
                        period_ids = self.pool.get('account.period').search(cr, uid, [('date_start','<=',asset_create_obj.register_date or time.strftime('%Y-%m-%d')),('date_stop','>=',asset_create_obj.register_date or time.strftime('%Y-%m-%d'))])
                        if period_ids:
                            period_id = period_ids[0]
                        asset = {
                                 'name': asect_seq,
                                 'register_date': asset_create_obj.register_date,
                                 'product_id' : asset_create_obj.product_id.id,
                                 'partner_id' : asset_create_obj.partner_id.id,
                                 'price_unit': asset_create_obj.price_unit,
                                 'company_id': asset_create_obj.company_id.id,
                                 'notes' : asset_create_obj.notes,
                                 'period_id' : period_id
                                 }
                        newid = self.pool.get('ineco.asset').create(cr, uid, asset)
                    self.pool.get('stock.move').write(cr, uid, context['active_id'], {'ineco_asset_register': True})
                    return {'type': 'ir.actions.act_window_close'}
                else:
                    raise osv.except_osv(_('Error !'), _('Repeatedly Register Asset'))
            else:
                raise osv.except_osv(_('Error !'), _('State product not done.'))                
                                     
stock_move_create_asset()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
