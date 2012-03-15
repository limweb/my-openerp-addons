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

class location_set_wizard(osv.osv_memory):

    _name = "stock.location.set.wizard"
    _description = "Browse Location Set"
    _columns = {
        'name': fields.char('Name',size=100),
        'location_set_id': fields.many2one('stock.location.set', 'Location Set', required=True),
#        'select_id': fields.integer('Select ID')
    }
    _defaults = {
        'name': '...'
    }
    
    def onchange_location(self, cr, uid, ids, location_set_id, context):
        #values = {'select_id': location_set_id}
        self.create(cr, uid, {'location_set_id':location_set_id})
        return {'value': values}
    
    def add_location_wizard(self, cr, uid, ids, context):
             
        if context is None:
            context = {}
        record_id = context.get('record_id', False)
        search = self.search(cr, uid, [])
        data = search.pop()            
        for line in self.browse(cr, uid, [data], context=context):
            for location in line.location_set_id.lines:
                self.pool.get('sale.branch.line').create(cr, uid, {
                    'sale_id': record_id,
                    'location_id': location.location_id.id
                })
        return {}
location_set_wizard()




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
