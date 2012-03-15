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
import decimal_precision as dp

from osv import fields,osv
from tools.translate import _

class product_product(osv.osv):

    def _get_foot_square(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = (line.product_width * line.product_length) / (304.79 * 304.79)
        return res

    def _get_product_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.product_ft2:
                res[line.id] = line.product_ft2 * line.qty_available * line.standard_price
            else:
                res[line.id] = line.qty_available * line.standard_price
        return res

    def _product_partner_ref(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for p in self.browse(cr, uid, ids, context=context):
            data = self._get_partner_code_name(cr, uid, [], p, context.get('partner_id', None), context=context)
            if not data['variants']:
                data['variants'] = p.variants
            if not data['code']:
                data['code'] = p.code
            if not data['name']:
                data['name'] = p.name
            res[p.id] = (data['name'] or '') + (data['variants'] and (' - '+data['variants']) or '')
        return res

    _name = "product.product"
    _inherit = "product.product"
    _description="Extension of Product for SR Advance Co.,Ltd."
    _columns = {
        'partner_ref' : fields.function(_product_partner_ref, method=True, type='char', string='Customer ref'),
        'thick': fields.many2one('product.thick', 'Thick', ondelete='restrict'),
        'product_width': fields.float('Width'),
        'product_length': fields.float('Length'),
        'product_ft2': fields.function(_get_foot_square, method=True, string='FT2', digits_compute= dp.get_precision('Sale Price')),
        'product_amount': fields.function(_get_product_amount, method=True, string='Amount', digits_compute= dp.get_precision('Sale Price')),
        'product_use_ft2': fields.boolean('Use FT2'),
        'product_use_m2': fields.boolean('Use Meter'),
        'no_print': fields.boolean('No Print Quotation'),
        'uom_category_id': fields.many2one('product.uom.categ', 'UOM Category', required=True, ondelete="restrict"),        
    }
    
    _defaults = {
        'no_print': False,
    }

    def onchange_glass(self, cursor, user, ids, thick_id, width, length ):
        if thick_id and width and length:
            thick = self.pool.get('product.thick')
            thick_obj = thick.browse(cursor,user,[thick_id])[0]
            thick_length = thick_obj.length
            return {'value': {'weight': thick_length * float(float(width)/1000) * float(float(length)/1000), 'weight_net': thick_length * float(float(width)/1000) * float(float(length)/1000)}}
        return False

    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        def _name_get(d):
            name = d.get('name','')
            code = d.get('default_code',False)
            if code:
                #original 
                #name = '[%s] %s' % (code,name)
                name = '%s' % (name)
            if d.get('variants'):
                name = name + ' - %s' % (d['variants'],)
            return (d['id'], name)

        partner_id = context.get('partner_id', False)

        result = []
        for product in self.browse(cr, user, ids, context=context):
            sellers = filter(lambda x: x.name.id == partner_id, product.seller_ids)
            if sellers:
                for s in sellers:
                    mydict = {
                              'id': product.id,
                              'name': s.product_name or product.name,
                              'default_code': s.product_code or product.default_code,
                              'variants': product.variants
                              }
                    result.append(_name_get(mydict))
            else:
                mydict = {
                          'id': product.id,
                          'name': product.name,
                          'default_code': product.default_code,
                          'variants': product.variants
                          }
                result.append(_name_get(mydict))
        return result
    
product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
