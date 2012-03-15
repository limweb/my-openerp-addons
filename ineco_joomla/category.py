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
import netsvc

import decimal_precision as dp

from osv import fields,osv
from tools.translate import _

class ineco_joomla_category(osv.osv):
    _name = 'ineco.joomla.category'
    _description = 'Joomla Category Class'
    _columns = {
        'name': fields.char('Category Name', size=254, required=True),
        'description': fields.char('Description', size=254),
        'category_id': fields.many2one('product.category', 'Product Category', required=True, ondelete='restrict'),
        'active': fields.boolean('Active'),
        'company_id': fields.many2one('res.company', 'Company', required=True, ondelete='restrict'),
        'user_id': fields.many2one("res.users","Recorder", required=True, ondelete='restrict'),
    }
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        'active': True,
    }
    _order = 'name'    

    def copy(self, cr, uid, id, default={}, context=None):
        master = self.read(cr, uid, id)
        name = master['name'] + " (copy)"
        default.update({
            'name': name,
        })
        return super(ineco_joomla_category, self).copy(cr, uid, id, default=default, context=context)
 
ineco_joomla_category()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: