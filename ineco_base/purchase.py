# -*- coding: utf-8 -*-
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
from datetime import datetime
from dateutil.relativedelta import relativedelta


import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp

class purchase_order(osv.osv):

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            max_tax = 0 
            vat_type = True
            for line in order.order_line:
               val1 += line.price_subtotal
               for tax in line.taxes_id:
                   max_tax = max(max_tax, tax.amount) 
                   vat_type = tax.include_base_amount = True
               #max_tax= max(max_tax, line.taxes_id.amount)
               for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, order.partner_address_id.id, line.product_id.id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)
            if vat_type: #exclude tax
                res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val1 * max_tax)
            else: #include tax
                res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val1 * (max_tax * 100 / (100 + (max_tax * 100))))                
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res

    _name = 'purchase.order'
    _inherit = 'purchase.order'
    _description = 'Change tax calculation in purchase order.'
    _columns = {
        'amount_untaxed': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Purchase Price'), string='Untaxed Amount',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax"),
        'amount_tax': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Purchase Price'), string='Taxes',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Purchase Price'), string='Total',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums",help="The total amount"),
    }
    
purchase_order()

class purchase_order_line(osv.osv):
    
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line'

    _columns = {
        'uom_category_id': fields.many2one('product.uom.categ', 'UOM Category', ondelete="restrict"),
    }

    def product_id_change(self, cr, uid, ids, pricelist, product, qty, uom,
            partner_id, date_order=False, fiscal_position=False, date_planned=False,
            name=False, price_unit=False, notes=False):
        if not pricelist:
            raise osv.except_osv(_('No Pricelist !'), _('You have to select a pricelist or a supplier in the purchase form !\nPlease set one before choosing a product.'))
        if not  partner_id:
            raise osv.except_osv(_('No Partner!'), _('You have to select a partner in the purchase form !\nPlease set one partner before choosing a product.'))
        if not product:
            return {'value': {'price_unit': price_unit or 0.0, 'name': name or '',
                'notes': notes or'', 'product_uom' : uom or False}, 'domain':{'product_uom':[]}}
        res = {}
        prod= self.pool.get('product.product').browse(cr, uid, product)
        product_uom_pool = self.pool.get('product.uom')
        lang=False
        if partner_id:
            lang=self.pool.get('res.partner').read(cr, uid, partner_id, ['lang'])['lang']
        context={'lang':lang}
        context['partner_id'] = partner_id

        prod = self.pool.get('product.product').browse(cr, uid, product, context=context)
        prod_uom_po = prod.uom_po_id.id
        if not uom:
            uom = prod_uom_po
        if not date_order:
            date_order = time.strftime('%Y-%m-%d')
        qty = qty or 1.0
        seller_delay = 0
        if uom:
            uom1_cat = prod.uom_id.category_id.id
            uom2_cat = product_uom_pool.browse(cr, uid, uom).category_id.id
            if uom1_cat != uom2_cat:
                uom = False

        prod_name = self.pool.get('product.product').name_get(cr, uid, [prod.id], context=context)[0][1]
        res = {}
        for s in prod.seller_ids:
            if s.name.id == partner_id:
                seller_delay = s.delay
                if s.product_uom:
                    temp_qty = product_uom_pool._compute_qty(cr, uid, s.product_uom.id, s.min_qty, to_uom_id=prod.uom_id.id)
                    uom = s.product_uom.id #prod_uom_po
                temp_qty = s.min_qty # supplier _qty assigned to temp
                if qty < temp_qty: # If the supplier quantity is greater than entered from user, set minimal.
                    qty = temp_qty
                    res.update({'warning': {'title': _('Warning'), 'message': _('The selected supplier has a minimal quantity set to %s, you cannot purchase less.') % qty}})
        qty_in_product_uom = product_uom_pool._compute_qty(cr, uid, uom, qty, to_uom_id=prod.uom_id.id)
        price = self.pool.get('product.pricelist').price_get(cr,uid,[pricelist],
                    product, qty_in_product_uom or 1.0, partner_id, {
                        'uom': uom,
                        'date': date_order,
                        })[pricelist]
        dt = (datetime.now() + relativedelta(days=int(seller_delay) or 0.0)).strftime('%Y-%m-%d %H:%M:%S')

        #if change manual price don't change old price
        if price_unit and price:
            price = price_unit 

        res.update({'value': {'price_unit': price, 'name': prod_name,
            'taxes_id':map(lambda x: x.id, prod.supplier_taxes_id),
            'date_planned': date_planned or dt,'notes': notes or prod.description_purchase,
            'product_qty': qty,
            'uom_category_id':prod.uom_id.category_id.id,
            'product_uom': prod.uom_po_id.id}})
        domain = {}

        taxes = self.pool.get('account.tax').browse(cr, uid,map(lambda x: x.id, prod.supplier_taxes_id))
        fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        res['value']['taxes_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, taxes)
        res2 = self.pool.get('product.uom').read(cr, uid, [prod.uom_id.id], ['category_id'])
        res3 = prod.uom_id.category_id.id
        domain = {'product_uom':[('category_id','=',res2[0]['category_id'][0])]}
        if res2[0]['category_id'][0] != res3:
            raise osv.except_osv(_('Wrong Product UOM !'), _('You have to select a product UOM in the same category than the purchase UOM of the product'))

        res['domain'] = domain
        return res

    def product_uom_change(self, cr, uid, ids, pricelist, product, qty, uom,
            partner_id, date_order=False, fiscal_position=False, date_planned=False,
            name=False, price_unit=False, notes=False):
        res = self.product_id_change(cr, uid, ids, pricelist, product, qty, uom,
                partner_id, date_order=date_order, fiscal_position=fiscal_position, date_planned=date_planned,
            name=name, price_unit=price_unit, notes=notes)
        if 'product_uom' in res['value']:
            if uom and (uom != res['value']['product_uom']) and res['value']['product_uom']:
                seller_uom_name = self.pool.get('product.uom').read(cr, uid, [res['value']['product_uom']], ['name'])[0]['name']
                #res.update({'warning': {'title': _('Warning'), 'message': _('The selected supplier only sells this product by %s') % seller_uom_name }})
            del res['value']['product_uom']
        if not uom:
            res['value']['price_unit'] = 0.0
        return res

    
purchase_order_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

