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
#################from itertools import groupby
from operator import itemgetter#############################################################

import time
import tools
import math

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from osv import osv, fields
import netsvc
import pooler
from tools.translate import _
import decimal_precision as dp
from osv.orm import browse_record, browse_null

from itertools import groupby
from operator import itemgetter

class ineco_mrp_workcenter_capacity(osv.osv):
    _name = "ineco.workcenter.capacity"
    _description = "Capacity of Workcenter"
    _columns = {
        'name': fields.char("Description", size=100, required=True),
        'categ_id': fields.many2one('product.category', 'Product Category', required=True, ondelete='restrict'),
        'cycle_per_hour': fields.float('Capacity Per Hour', digits_compute=dp.get_precision('Account'), required=True),
        'workcenter_id': fields.many2one('mrp.workcenter', 'Workcenter', ondelete='restrict'),
    }
    _defaults = {
        'cycle_per_hour': 0,
    }
    _order = "name"
    _sql_constraints = [
        ('workcenter_capacity_uniq', 'unique (workcenter_id,categ_id)', 'Product category must be unique!')
    ]

    def onchange_categ_id(self, cr, uid, ids, categ_id, context=None):
        """ Changes UoM and name if product_id changes.
        @param namefrom itertools import groupby
from operator import itemgetter: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        if categ_id:
            prod = self.pool.get('product.category').browse(cr, uid, categ_id, context=context)
            v = {}
            if prod:
                v['name'] = prod.name
            return {'value': v}
        return {}

ineco_mrp_workcenter_capacity()

class mrp_workcenter(osv.osv):
    
    _name = "mrp.workcenter"
    _inherit = "mrp.workcenter"
    _description = "Include Capacity of Workcenter"
    _columns = {
        'capacity_lines': fields.one2many('ineco.workcenter.capacity', 'workcenter_id', 'Capacity Lines'),
        'priority': fields.integer('Priority', required=True)
    }
    _defaults = {
        'priority': 1,
    }
    _orderby = "priority"
    
    def _get_capacity_hours(self, cr, uid, ids, date, context=None):
        workcenter = self.pool.get('mrp.workcenter').browse(cr, uid, ids)[0]
        dt_from = datetime.strptime(date[:10], '%Y-%m-%d')
        dt_to = datetime.strptime(date[:10], '%Y-%m-%d')        
        capacity_hour = workcenter.resource_id.calendar_id.ineco_interval_hours_get(dt_from, dt_to)
        return capacity_hour
    
    def _get_planned_capacity_hours(self, cr, uid, ids, date, context=None):
        capacity_hour = 0
        capobj = self.pool.get('ineco.workcenter.capacity.view')
        cap_ids = capobj.search(cr, uid,[('workcenter_id','=',ids),('date_planned','=',date[:10])] )
        if cap_ids:
            capacity = capobj.browse(cr, uid, cap_ids)[0]
            capacity_hour = capacity.hour_actual
            #print "ID: %s, NAME: %s, DATE: %s" % (ids, capacity.workcenter_id.name, date)
        return capacity_hour
    
    
    def _get_capacity(self, cr, uid, ids, product, qty=1, context=None):
        capacity_ids = self.pool.get('ineco.workcenter.capacity').search(cr, uid, [('workcenter_id','=',ids),('categ_id','=',product.categ_id.id)])
        capacity_hour = 0
        if capacity_ids:
            capacity = self.pool.get('ineco.workcenter.capacity').browse(cr, uid, capacity_ids)[0]
            capacity_hour = qty / capacity.cycle_per_hour or 0.00 
        return capacity_hour
    
mrp_workcenter()

class mrp_production_workcenter_line(osv.osv):

    def _hour_plan(self, cr, uid, ids, field_name, arg, context=None):
        """ Finds ending date.
        @return: Dictionary of values.
        """
        ops = self.browse(cr, uid, ids, context=context)

        res = {}

        for op in ops:
            res[op.id] = op.hour
            if op.workcenter_id and op.production_id:
                capacity_ids = self.pool.get('ineco.workcenter.capacity').search(cr, uid, [('workcenter_id','=',op.workcenter_id.id),('categ_id','=',op.production_id.product_id.categ_id.id)])
                if capacity_ids:
                    capacity = self.pool.get('ineco.workcenter.capacity').browse(cr, uid, capacity_ids)[0]
                    res[op.id] = op.cycle / capacity.cycle_per_hour or 0.00
                else:
                    res[op.id] = op.hour
        return res

    def ineco_get_date_end(self, cr, uid, ids, field_name, arg, context=None):
        ops = self.browse(cr, uid, ids, context=context)
        #date_and_hours_by_cal = [(op.date_planned, op.hour, op.workcenter_id.calendar_id.id) for op in ops if op.date_planned]
        #change op.hour -> op.hour_plan
        date_and_hours_by_cal = [(op.date_planned, op.hour_plan, op.workcenter_id.calendar_id.id) for op in ops if op.date_planned]
        #print date_and_hours_by_cal
        intervals = self.pool.get('resource.calendar').interval_get_multi(cr, uid, date_and_hours_by_cal)    

        res = {}
        for op in ops:
            res[op.id] = False
            if op.date_planned:
                #i = intervals.get((op.date_planned, op.hour, op.workcenter_id.calendar_id.id))
                #change op.hour -> op.hour_plan
                i = intervals.get((op.date_planned, op.hour_plan, op.workcenter_id.calendar_id.id))
                #print "%s %s " % (op.date_planned,i)
                if i:
                    res[op.id] = i[-1][1].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    res[op.id] = op.date_planned
        return res

    _name = 'mrp.production.workcenter.line'
    _inherit = 'mrp.production.workcenter.line'
    _description = 'Extended of Work Order'

    _columns = {
        'hour_plan': fields.function(_hour_plan, method=True, string='Plan Capacity', type='float', digits=(16,2)),
        'actual_hour': fields.float('Actual Capacity Plan', digits=(16,2)),
        'date_planned_end': fields.function(ineco_get_date_end, method=True, string='End Date', type='datetime'),
    }

mrp_production_workcenter_line()

def rounding(f, r):
    import math
    if not r:
        return f
    return math.ceil(f / r) * r

class mrp_bom(osv.osv):
    _name = "mrp.bom"
    _inherit = "mrp.bom"
    _description = "change hour calculation in BOM explode"
    _columns = {
    }

    def _bom_explode(self, cr, uid, bom, factor, properties=[], addthis=False, level=0):
        """ Finds Products and Work Centers for related BoM for manufacturing order.
        @param bom: BoM of particular product.
        @param factor: Factor of product UoM.
        @param properties: A List of properties Ids.
        @param addthis:from itertools import groupby
from operator import itemgetter If BoM found then True else Faop.workcenter_id.resource_id.calendar_id.ineco_interval_hours_get(dt_from, dt_to )lse.
        @param level: Depth level to find BoM lines starts from 10.
        @return: result: List of dictionaries containing product details.
                 result2: List of dictionaries containing Work Center details.
        """
        factor = factor / (bom.product_efficiency or 1.0)
        factor = rounding(factor, bom.product_rounding)
        if factor < bom.product_rounding:
            factor = bom.product_rounding
        result = []
        result2 = []
        phantom = False
        if bom.type == 'phantom' and not bom.bom_lines:
            newbom = self._bom_find(cr, uid, bom.product_id.id, bom.product_uom.id, properties)
            if newbom:
                res = self._bom_explode(cr, uid, self.browse(cr, uid, [newbom])[0], factor*bom.product_qty, properties, addthis=True, level=level+10)
                result = result + res[0]
                result2 = result2 + res[1]
                phantom = True
            else:
                phantom = False
        if not phantom:
            if addthis and not bom.bom_lines:
                result.append(
                {
                    'name': bom.product_id.name_template,
                    'product_id': bom.product_id.id,
                    'product_qty': bom.product_qty * factor,
                    'product_uom': bom.product_uom.id,
                    'product_uos_qty': bom.product_uos and bom.product_uos_qty * factor or False,
                    'product_uos': bom.product_uos and bom.product_uos.id or False,
                })
            if bom.routing_id:
                for wc_use in bom.routing_id.workcenter_lines:
                    wc = wc_use.workcenter_id
                    d, m = divmod(factor, wc_use.workcenter_id.capacity_per_cycle)
                    mult = (d + (m and 1.0 or 0.0))
                    cycle = mult * wc_use.cycle_nbr
                    #change hour this line
                    capacity_ids = self.pool.get('ineco.workcenter.capacity').search(cr, uid, [('workcenter_id','=',wc.id),('categ_id','=',bom.product_id.categ_id.id)])
                    capacity = float(wc_use.hour_nbr*mult + ((wc.time_start or 0.0)+(wc.time_stop or 0.0)+cycle*(wc.time_cycle or 0.0)) * (wc.time_efficiency or 1.0))
                    hour_plan = capacity 
                    #print capacity_ids
                    if capacity_ids:
                        capacity = self.pool.get('ineco.workcenter.capacity').browse(cr, uid, capacity_ids)[0]
                        hour_plan = cycle / capacity.cycle_per_hour or 0.00
                    #end change 25-05-2011
                    result2.append({
                        'name': tools.ustr(wc_use.name) + ' - '  + tools.ustr(bom.product_id.name_template),
                        'workcenter_id': wc.id,
                        'sequence': level+(wc_use.sequence or 0),
                        'cycle': cycle,
                        'hour': hour_plan,
                    })
            for bom2 in bom.bom_lines:
                res = self._bom_explode(cr, uid, bom2, factor, properties, addthis=True, level=level+10)
                result = result + res[0]
                result2 = result2 + res[1]
        return result, result2

mrp_bom()

class ineco_workcenter_capacity_draft(osv.osv):
    _name = "ineco.workcenter.capacity.draft"
    _description = "Draft Workcenter Capacity"
    _auto = False
    _columns = {
        'workcenter_id': fields.many2one('mrp.workcenter', 'Work Center', readonly=True, ondelete='restrict'),
        'date_planned': fields.date('Date Planned', readonly=True),
    }

    def init(self, cr):
	    cr.execute("""
            create or replace view ineco_workcenter_capacity_draft_view as (
                select distinct w.id as workcenter_id, date_trunc('day',m.date_planned) as date_planned from mrp_production_workcenter_line m
                left outer join resource_resource w on m.workcenter_id = w.id )
	    """)

ineco_workcenter_capacity_draft()

class ineco_workcenter_capacity(osv.osv):

    def _get_hour(self, cr, uid, ids, field_name, arg, context=None):
        ops = self.browse(cr, uid, ids, context=context)

        res = {}

        for op in ops:
            if op.workcenter_id:
                dt_from = datetime.strptime(op.date_planned[:10], '%Y-%m-%d')
                dt_to = datetime.strptime(op.date_planned[:10], '%Y-%m-%d')
                #print "%s %s" % (dt_from, dt_to)
                res[op.id] = op.workcenter_id.resource_id.calendar_id.ineco_interval_hours_get(dt_from, dt_to )
        return res

    def _get_hour_actual(self, cr, uid, ids, field_name, arg, context=None):
        ops = self.browse(cr, uid, ids, context=context)

        res = {}

        for op in ops:
            if op.workcenter_id:
                cr.execute("select * from mrp_production_workcenter_line "\
                           "where workcenter_id = %s and date_trunc('day', date_planned) = '%s'" % (op.workcenter_id.id, op.date_planned[:10]) )
                capacity_ids = map(itemgetter(0), cr.fetchall())
                #capacity_ids = self.pool.get('mrp.production.workcenter.line').search(cr, uid, [('workcenter_id','=',op.workcenter_id.id),('date_planned','=',op.date_planned)])
                if capacity_ids:
                    
                    new_hour = 0.0
                    for capacity in self.pool.get('mrp.production.workcenter.line').browse(cr,uid,capacity_ids):
                        new_hour += capacity.hour
                    res[op.id] = new_hour
                else:
                    res[op.id] = 0
        return res

    _name = "ineco.workcenter.capacity.view"
    _description = "Workcenter Capacity"
    _auto = False
    _columns = {
        'workcenter_id': fields.many2one('mrp.workcenter', 'Work Center', readonly=True, ondelete='restrict'),
        'date_planned': fields.date('Date Planned', readonly=True),
        'hour_per_day': fields.function(_get_hour, method=True, string='Hours Per Day', type='float', digits=(16,2)),
        'hour_actual': fields.function(_get_hour_actual, method=True, string="Hour Planned", type='float', digits=(16,2)),
    }

    def init(self, cr):
	    cr.execute("""
            create or replace view ineco_workcenter_capacity_view as (
                select id, (a[id]).*
                from (
                    select a, generate_series(1, array_upper(a,1)) as id
                    	from (
                    		select array (
                    			select ineco_workcenter_capacity_draft_view from ineco_workcenter_capacity_draft_view
                    			order by date_planned
                    		) as a
                	) b
                ) c
            )    
	    """)

ineco_workcenter_capacity()

class resource_calendar(osv.osv):
    _name = "resource.calendar"
    _inherit = "resource.calendar"
    _description = "Extended for Resource Calendar"
    _columns = {
    }

    def ineco_interval_hours_get(self, cr, uid, id, dt_from, dt_to, resource=False):
        if not id:
            return 0.0
        dt_leave = self._get_leaves(cr, uid, id, resource)
        hours = 0.0

        current_hour = dt_from.hour
        #print dt_from
        cr.execute("select hour_from,hour_to from resource_calendar_attendance where dayofweek='%s' and calendar_id=%s order by dayofweek, hour_from", (dt_from.weekday(),id[0]))
        der =  cr.fetchall()
        for (hour_from,hour_to) in der:
            if hours != 0.0:#For first time of the loop only,hours will be 0
                current_hour = hour_from
            leave_flag = False
            if (hour_to>=current_hour):
                dt_check = dt_from.strftime('%Y-%m-%d')
                for leave in dt_leave:
                    if dt_check == leave:
                        dt_check = datetime.strptime(dt_check, "%Y-%m-%d") #+ timedelta(days=1)
                        leave_flag = True

                if leave_flag:
                    break
                else:
                    d1 = datetime(dt_from.year, dt_from.month, dt_from.day, int(math.floor(hour_from)), int((hour_from%1) * 60))
                    #print dt_from
                    if hour_to == 24:
                        hour_to = 23;
                    d2 = datetime(dt_from.year, dt_from.month, dt_from.day, int(math.floor(hour_to)), int((hour_to%1) * 60))

                    if hours != 0.0:#For first time of the loop only,hours will be 0
                        d1 = datetime(dt_from.year, dt_from.month, dt_from.day, int(math.floor(current_hour)), int((current_hour%1) * 60))

                    if dt_from.day == dt_to.day:
                        if hour_from <= dt_to.hour <= hour_to:
               #             d2 = dt_to
                             dt_to = d2
                    dt_from = d2
                    hours += (d2-d1).seconds
                    #print "%s %s" % (d2, d1)            

        return (hours/3600)
    
    def interval_get_multi(self, cr, uid, date_and_hours_by_cal, resource=False, byday=True):
        def group(lst, key):
            lst.sort(key=itemgetter(key))
            grouped = groupby(lst, itemgetter(key))
            return dict([(k, [v for v in itr]) for k, itr in grouped])
        # END group
        cr.execute("select calendar_id, dayofweek, hour_from, hour_to from resource_calendar_attendance order by dayofweek, hour_from")
        hour_res = cr.dictfetchall()
        hours_by_cal = group(hour_res, 'calendar_id')

        results = {}

        for d, hours, id in date_and_hours_by_cal:
            dt_from = datetime.strptime(d, '%Y-%m-%d %H:%M:%S')
            if not id:
                #print "not id"
                td = int(hours)*3
                results[(d, hours, id)] = [(dt_from, dt_from + timedelta(hours=td))]
                continue

            dt_leave = self._get_leaves(cr, uid, id, resource)

            todo = hours
            result = []
            maxrecur = 100
            current_hour = dt_from.hour
            current_minute = dt_from.minute
            while (todo > 0) and maxrecur:
                for (hour_from,hour_to) in [(item['hour_from'], item['hour_to']) for item in hours_by_cal[id] if item['dayofweek'] == str(dt_from.weekday())]:
                    leave_flag  = False
                    if (hour_to>current_hour) and (todo>0):
                        m = max(hour_from, current_hour)
                        hour_length = hour_to - hour_from
                        if (hour_to-m)>todo:
                            hour_to = m+todo #m 08:00 + todo 2hrs
                        dt_check = dt_from.strftime('%Y-%m-%d')
                        for leave in dt_leave:
                            if dt_check == leave:
                                dt_check = datetime.strptime(dt_check, '%Y-%m-%d') + timedelta(days=1)
                                leave_flag = True
                        if leave_flag:
                            break
                        else:
                            new_m = 0
                            new_m_minute = current_minute
                            if int((m%1)*60)+current_minute >= 60:
                                m += 1
                                new_m_minute = int((m%1)*60)+current_minute - 60
                            new_m = m 

                            new_hour_to = 0
                            new_hour_minute = current_minute
                            if int((hour_to%1)*60)+current_minute >= 60:
                                hour_to += 1
                                new_hour_minute = int((hour_to%1)*60) + current_minute - 60
                            new_hour_to = hour_to
                            #print 'new_m: %s, new_m_minute: %s, -->%s' % (new_m, new_m_minute, int((new_m%1) * 60)+new_m_minute)
                            #print 'new_hour_to: %s, new_hour_minute: %s, -->%s' % (new_hour_to, new_hour_minute, int((new_hour_to%1) * 60)+new_hour_minute)
                            
                            d1 = datetime(dt_from.year, dt_from.month, dt_from.day, int(math.floor(new_m)), new_m_minute)
                            d2 = datetime(dt_from.year, dt_from.month, dt_from.day, int(math.floor(new_hour_to)), new_hour_minute)
                            
                            result.append((d1, d2))
                            current_hour = hour_to
                            #todo -= (hour_to - m)
                            todo -= hour_length
                dt_from += timedelta(days=1)
                current_hour = 0
                maxrecur -= 1
            results[(d, hours, id)] = result
        return results

resource_calendar()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

