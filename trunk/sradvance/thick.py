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

class product_thick(osv.osv):

    def _complete_name(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            try:
                res[line.id] = '%s mm.' % (line.length)
            except:
                res[line.id] = line.name
        return res

    _name = "product.thick"
    _description = "Thick of Product"
    _order = 'length'

    _columns = {
        'name': fields.char('Thickness', size=32, select=True, required=True, translate=True),
        'length': fields.float('Length (mm.)', digits=(8,2), required=True),
        'complete_name': fields.function(_complete_name, method=True, type='char', string='Glass Thickness'),
    }

    _defaults = {
        
    }

    _sql_constraints = [
        ('thick_length_uniq', 'unique (length)', 'Length of thickness must me unique.')
    ]
    
    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context={}
        previous_lang = context.get('lang') 
        thick = self.read(cr, uid, id, ['name','length'], context=context)
        if not default:
            default = {}
        default = default.copy()
        default['length'] = thick['length'] + 0.01
        default['name'] = thick['name'] + _(' (copy)')

        return super(product_thick, self).copy(cr, uid, id, default=default, context=context)
    
product_thick()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
