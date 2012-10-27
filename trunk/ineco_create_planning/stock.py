# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 INECO LTD, PARTNERSHIP (<http://www.ineco.co.th>).
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

import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp
import netsvc

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from operator import itemgetter
from itertools import groupby

class stock_move(osv.osv):
    
    _inherit = "stock.move"
    
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if isinstance(ids, int):
            ids = [ids]
        for sm in self.pool.get("stock.move").browse(cr, uid, ids):
            plan_obj = self.pool.get('stock.planning')
            warehouse_obj = self.pool.get('stock.warehouse')
            period_obj = self.pool.get('stock.period')
            #warehouse_id, period_id, product_id, product_uom
            location_id = sm.location_dest_id 
            if location_id.usage in ('customer','internal'):
                warehouse_ids = False
                
                if location_id.usage == 'customer':
                    warehouse_ids = warehouse_obj.search(cr, uid, [('lot_stock_id','=',location_id.id)])
                elif location_id.usage == 'internal':
                    stock_ids = self.pool.get('stock.location').search(cr, uid, [('name','=','Stock')])
                    warehouse_ids = warehouse_obj.search(cr, uid, [('lot_stock_id','=',stock_ids[0])])

                if not warehouse_ids:
                    warehouse_data = {
                        'name': 'Warehouse (%s)' % location_id.name,
                        'lot_input_id': location_id.id,
                        'lot_stock_id': location_id.id,
                        'lot_output_id': location_id.id,
                    }
                    warehouse_id = warehouse_obj.create(cr, uid, warehouse_data)
                else:
                    warehouse_id = warehouse_ids[0]
                product_id = sm.product_id.id
                product_uom_id = sm.product_id.uom_id.id

                period_sql = """
                    select
                      (select id from stock_period 
                       where date_start <= sm.date_expected and date_stop >= sm.date_expected) as stock_period_id
                    from stock_picking sp
                    join stock_move sm on sp.id = sm.picking_id
                    where sm.id = %s 
                    """
                cr.execute(period_sql % (sm.id))
                period_ids = map(lambda x: x[0], cr.fetchall())
                if period_ids:
                    period_id = period_ids[0]
                    plan_ids = plan_obj.search(cr, uid, [('warehouse_id','=',warehouse_id),
                                              ('product_id','=',product_id),('product_uom','=',product_uom_id),('period_id','=',period_id)])
                    if not plan_ids:
                        plan_data = {
                            'warehouse_id': warehouse_id,
                            'product_id': product_id,
                            'product_uom': product_uom_id,
                            'period_id': period_id,
                        }
                        plan_obj.create(cr, uid, plan_data )
                else:
                    message = _("Date expected '%s' not in Stock.Period.") % sm.date_expected
                    self.log(cr, uid, sm.id, message)                        
                            
        return super(stock_move, self).write(cr, uid, ids, vals, context=context)
    
stock_move()