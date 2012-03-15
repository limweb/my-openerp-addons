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

import wizard
from osv import osv
import pooler
from osv import fields
import time

from itertools import groupby
from operator import itemgetter
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def _launch_wizard(self, cr, uid, data, context=None):
    pool = pooler.get_pool(cr.dbname)
    
    saleorders = pool.get('sale.order').browse(cr, uid, data['ids'])
    request_date = saleorders[0].requested_date[:10]
    workcenter_load = {}
    for sale in saleorders:
        for line in sale.order_line:
            for linework in line.additional_line:
                qty = linework.product_qty
                product = linework.product_id
                product_qty = line.product_uom_qty
                bom_ids = pool.get('mrp.bom').search(cr, uid, [('product_id','=',product.id),('type','=','normal'),('bom_id','=',False)])
                if bom_ids:
                    bom = pool.get('mrp.bom').browse(cr, uid, bom_ids)[0]
                    if bom.routing_id:
                        for wc_line in bom.routing_id.workcenter_lines:
                            workcenter = wc_line.workcenter_id
                            wk_caps = workcenter._get_capacity(product, qty*product_qty)
                            if not workcenter_load.has_key(workcenter.id):
                                workcenter_load.update({workcenter.id: wk_caps})
                            else:
                                new_caps = workcenter_load[workcenter.id] + wk_caps
                                workcenter_load.update({workcenter.id: new_caps})
                            #print workcenter_load
    cr.execute( ("delete from sale_order_line_plan where order_id = %d " % data['id']) )
    for workcenter_id, capacity in workcenter_load.iteritems():                    
        workcenter_obj = pool.get('mrp.workcenter')
        workcenter_ids = workcenter_obj.browse(cr, uid, [workcenter_id])
        if workcenter_ids:
            workcenters = workcenter_ids[0]
            wk_capacities = workcenters._get_capacity_hours(request_date)
            wk_load = workcenters._get_planned_capacity_hours(request_date)
            wk_newload = wk_load + capacity
            obj = pool.get('sale.order.line.plan')
            obj.create(cr, uid, {
                'order_id': data['id'],
                'workcenter_id': workcenters.id,
                'name': workcenters.name,
                'seq': workcenters.priority,
                'capacity': capacity,
                'capacity_planned': wk_capacities,
                'capacity_loaded': wk_load,
            })
    cr.execute(("select * from sale_order_line_plan where order_id = %s order by seq desc" % data['id']) )
    plan_ids = map(itemgetter(0), cr.fetchall())
    request_date_new = datetime.strptime(request_date[:10], '%Y-%m-%d')
    if plan_ids:                
        for plan in pool.get('sale.order.line.plan').browse(cr, uid, plan_ids):
            finish_date = request_date_new
            if plan.capacity_loaded + plan.capacity <= plan.capacity_planned:
                plan.write({'date_start':request_date_new,'date_finish':finish_date,'capacity_loaded':plan.capacity_loaded + plan.capacity})
            else:
                hasChange = False
                wk_load_sum = 0
                while (not hasChange) and (request_date_new > datetime.strptime(saleorders[0].date_order[:10], '%Y-%m-%d')):                            
                    request_date = datetime.strftime(request_date_new, '%Y-%m-%d')
                    wk_load = plan.workcenter_id._get_planned_capacity_hours(request_date)
                    wk_capacities = plan.workcenter_id._get_capacity_hours(request_date)
                    wk_load_sum += (wk_capacities - wk_load)
                    #print 'WC:%s, Date:%s, %s' % (plan.workcenter_id.name, request_date_new, wk_load_sum)
                    if plan.capacity <= wk_load_sum:
                        plan.write({'date_start':request_date_new,'date_finish':finish_date,'capacity_loaded':wk_load_sum})
                        hasChange = True
                    else:
                        request_date_new -= timedelta(days=1)
    
    return {}


class launch_map(wizard.interface):

    states= {'init' : {'actions': [],
                       'result':{'type':'action',
                                 'action': _launch_wizard,
                                 'state':'end'}
                       }
             }

launch_map('finding_schedule_finish_date')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

