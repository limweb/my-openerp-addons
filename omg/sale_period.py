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

# 09-02-2012     POP-001    Change way to compute period length.
# 05-03-2012     POP-002    Change size 32 -> 64
# 14-03-2012     POP-003    Add Warehouse Lock cannot confirm Sale Order
# 27-04-2012     POP-004    Add Period Category

import time
import netsvc

import decimal_precision as dp

from osv import fields,osv
from tools.translate import _

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class omg_sale_period_category(osv.osv):
    _name = "omg.sale.period.category"
    _description = "Period Category"
    _order = 'name'

    _columns = {
        #POP-004
        'name':fields.char('Name', size=64, required=True),
    }
omg_sale_period_category()

class omg_sale_period(osv.osv):

    def _day_count(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            DATETIME_FORMAT = "%Y-%m-%d"
            from_dt = datetime.strptime(line.date_start, DATETIME_FORMAT)
            to_dt = datetime.strptime(line.date_finish, DATETIME_FORMAT)
            timedelta = to_dt - from_dt 
            diff_day = timedelta.days + 1 #+ line.addup
            res[line.id] = diff_day
        return res

    #POP-001
    def _day_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            DATETIME_FORMAT = "%Y-%m-%d"
            from_dt = datetime.strptime(line.date_start, DATETIME_FORMAT)
            to_dt = datetime.strptime(line.date_finish, DATETIME_FORMAT)
            timedelta = to_dt - from_dt 
            diff_day = timedelta.days + 1 + line.addup
            res[line.id] = diff_day
        return res

    _name = "omg.sale.period"
    _description = "Sale Period Master of OMG Holding (Thailand) Co.,Ltd."
    _order = 'name'

    _columns = {
        #POP-002
        'name':fields.char('Period ID', size=64, select=True, required=True),
        'description': fields.char('Description', size=100, select=True, required=True),
        'date_start':fields.date("Date From", select=True, required=True),
        'date_finish':fields.date("Date To", select=True, required=True),
        'date_length': fields.function(_day_count, method=True, string='Day Counts', digits_compute= dp.get_precision('Sale Price')),
        #POP-001
        'date_total': fields.function(_day_total, method=True, string='Day Total', digits_compute= dp.get_precision('Sale Price')),
        'move_ids': fields.one2many('stock.move','period_id','Moves'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'addup' : fields.integer('Add Up Day (Estimate)'),
        #POP-003
        'warehouse_lock': fields.boolean('Warehouse Lock'),
        'category_id': fields.many2one('omg.sale.period.category', 'Category'),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,        
        'addup' : 0,
        'warehouse_lock': False,
    }
    
omg_sale_period()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
