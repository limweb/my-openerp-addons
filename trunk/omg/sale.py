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

# Date             ID         Message
# 12-12-2011       POP-001    Change Stock.Move Destination ID Gen. By BOM to Store Location
# 09-01-2012       POP-002    Add Logistic Path in stock.picking
# 31-01-2012       POP-003    Change how to delivery date, arrival date
# 05-02-2012       POP-004    Default Value use_location_qty in sale.order.line
# 05-02-2012       POP-005    Change Sampling Computation
# 08-02-2012       POP-006    Add omg.sale.group.special
# 09-02-2012       POP-007    Change Ratio Input Process
# 09-02-2012       POP-008    Change Period Date Count (date_legnth->date_total)
# 12-02-2012       POP-009    Add Rounding 
# 16-02-2012       POP-010    Add Class Stock Special Group
# 22-02-2012       POP-011    Add Branch Location Estimate in sale order
# 12-02-2012       POP-012    Change price computation in sale order.
# 13-02-2012       POP-013    Ineco Delivery Date = False
# 16-02-2012       POP-014    Force Draft State
# 02-03-2012       POP-015    Add Create Invoice 
# 02-03-2012       POP-016    Add Create Invoice Line
# 05-04-2012       POP-017    Add Equipment Process
# 11-04-2012       POP-018    Add Period_ID In sale.order
# 17-04-2012       POP-019    Add Product Mapping Process
# 23-04-2012       POP-020    Add Bug in Period Count
# 23-04-2012       POP-021    Raise when sale order cancel over lock period.
# 23-04-2012       POP-022    Add Price in Stock Move when Cash Advance
# 07-05-2012       POP-023    Use Full Warehouse UOM
# 02-07-2012       DAY-001    Update Use Full Warehouse UOM
# 05-07-2012       POP-024    Add Adjust Stock Store
# 17-07-2012       DAY-002    Group Invoice
# 23-07-2012       DAY-003    Add Class Cash Advance Other
# 29-07-2012       POP-025    Add Sale Order Line Branch 
#                  POP-026    Add Delivery Type
# 30-07-2012       DAY-004    Bug Cancel Sale Order
# 30-07-2012       DAY-005    Add Fields Locations Type
# 09-08-2012       POP-027    Add Sale Data
# 14-08-2012       DAY-006    Add Specific Booth Type
# 25-08-2012       DAY-007    Add Material Cash Advance

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

import time
import netsvc
import sale_period
import sale

import decimal_precision as dp

from osv import fields,osv
from tools.translate import _
import pooler
import tools 

from operator import itemgetter

#POP-027

#POP-026
class omg_delivery_type(osv.osv):
    _name = "omg.delivery.type"
    _description = "Delivery Kind"
    _columns = {
        'name': fields.char('Code', size=50, required=True),
        'description': fields.char('Description',size=250),
    }
    _sql_constraints = [
        ('code_unique', 'unique (name)', 'The code of the Delivery Type must be unique!')
    ]
    
omg_delivery_type()

#POP-025
class sale_order_line_branch(osv.osv):
    _name = 'sale.order.line.branch'
    _description = 'Sale Line in Branch'
    _columns = {
        'name': fields.char('Description', size=250, required=True),
        'order_id': fields.many2one('sale.order','Sale Order',required=True),
        'sale_line_id': fields.many2one('sale.order.line','Line',required=True),
        'location_id': fields.many2one('stock.location','Location',required=True),
        'delivery_type_id': fields.many2one('omg.delivery.type','Delivery Type'),
        'process': fields.boolean('Process'),
        'product_id': fields.many2one('product.product','Product',required=True),
        'pm_qty': fields.float('PM Qty', digits=(8,2), required=True),
        'pm_uom_id': fields.many2one('product.uom','PM Uom', required=True),
        'note': fields.char('Note', size=250),
    }
    _defaults = {
        'process': False,
        'note': False,
        'pm_qty': 0,        
    }
    _sql_constraints = [
        ('line_location_product_unique', 'unique (sale_line_id, location_id, product_id)', 'Data must be unique!')
    ]    
sale_order_line_branch()


class sale_period_line(osv.osv):

    def _get_date_start(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.period_id.date_start
        return res

    def _get_date_finish(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.period_id.date_finish
        return res

    def _get_date_length(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.period_id.date_length
        return res

    def _get_date_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.period_id.date_total
        return res

    _name = "sale.period.line"
    _description = "Extend sale period for Sale Order"

    _columns = {
        'sale_id': fields.many2one('sale.order','Sale Order', ondelete="restrict"),
        'period_id': fields.many2one('omg.sale.period','Period', ondelete="restrict"),
        'description': fields.char('Description', size=64),
        'date_start': fields.function(_get_date_start, method=True, type='datetime', string='Date From'),
        'date_finish': fields.function(_get_date_finish, method=True, type='datetime', string='Date To'),
        'date_length': fields.function(_get_date_length, method=True, type='integer', string='Day Counts'),
        'date_total': fields.function(_get_date_total, method=True, type='integer', string='Day Total'),
    }    

    _sql_constraints = [
        ('sale_period_line_unique','unique (sale_id, period_id)', 'Period Line must me unique.')
    ]
    

sale_period_line()

#DAY-003
class sale_cash_advance_other_line(osv.osv):
    _name = 'sale.cash.advance.other.line'
    _description = 'Cash Advance Other from Location'
    _columns = {
        'sale_id': fields.many2one('sale.order','Sale Order',ondelete="restrict"),
        'cash_advance_other_id':fields.many2one('stock.location.cash.advance.other','Cash Advance Other',ondelete="restrict"),
        'location_id': fields.many2one('stock.location','Location', required=True, ondelete="restrict"),
        'product_id': fields.many2one('product.product','Cash Advance',required=True),
        'amount': fields.float('Amount',required=True),                      
    }
    def onchange_product_id(self, cr, uid, ids, product_id):
        v = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            v['amount'] = product.list_price
        return {'value': v}
        
sale_cash_advance_other_line()


#DAY-007
class sale_cash_advance_material_line(osv.osv):
    _name = 'sale.cash.advance.material.line'
    _description = 'Material Cash Advance'
    _columns = {
        'sale_id': fields.many2one('sale.order','Sale Order',ondelete="restrict"),
        'location_id': fields.many2one('stock.location','Location', required=True, ondelete="restrict"),
        'amount': fields.float('Amount',required=True),                  
    }   
sale_cash_advance_material_line()
    
#POP-006
class omg_sale_group_special(osv.osv):
    _name = 'omg.sale.group.special'
    _description = "Special Group for OMG Location"
    _columns = {
        'name': fields.char('Group Name', size=128, required=True),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'active': True,
    }
omg_sale_group_special()

#POP-007 
class omg_stock_location_group_special(osv.osv):
    _name = 'omg.stock.location.group.special'
    _description = "Location Group Special"
    _columns = {
        'name': fields.char('Description', size=100),
        'location_id': fields.many2one('stock.location', 'Location'),
        'group_id': fields.many2one('omg.sale.group.special', 'Group'),
    }
omg_stock_location_group_special()

class sale_branch_line(osv.osv):

    def _get_locationname(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.location_id.complete_name
        return res

    _name = "sale.branch.line"
    _description = "Sale Branch Line extend for Sale Order"

    _columns = {
        'sale_id': fields.many2one('sale.order','Sale Order', ondelete="restrict"),
        'location_id': fields.many2one('stock.location','Location', required=True, ondelete="restrict"),
        'location_name': fields.function(_get_locationname, method=True, type='char', string='Location Name'),
        'area': fields.char('Area',size=32),
        'group': fields.char('Group',size=32),
        'department': fields.char('Department',size=64),
        'estimate': fields.integer('Estimate'),
#        DAY-005
        'location_type_id': fields.related('location_id', 'location_type_id', type='many2one', relation='omg.sale.location.type', store=True, string='Type'),        
#        DAY-006
        'specific_booth_type_id': fields.related('location_id','specific_booth_type_id', type='many2one',relation='omg.sale.location.booth.type', store=True, string='Booth Type'),
    }    
    
    _defaults = {
        'estimate': 0
    }

    _sql_constraints = [
        ('sale_branch_unique','unique (sale_id, location_id)', 'Branch must me unique.')
    ]

    def _get_max_service(self, cr, uid, location_id, service_categ_id, context=None):
        result = 1000
        service_ids = self.pool.get('ineco.stock.location.category.max').search(cr, uid, [('location_id','=',location_id),('category_id','=',service_categ_id)])
        if service_ids:
            service = self.pool.get('ineco.stock.location.category.max').browse(cr, uid, service_ids)[0]
            result = service.quantity
        return result

    def _can_booking(self, cr, uid, location_id, category_id, period_id, service_categ_id, context=None):
        booking_ids = self.pool.get('stock.location.booking').search(cr, uid,[('location_id','=',location_id),('period_id','=',period_id),('category_id','=',category_id),('state','=','done')])
        max_ids = self.pool.get('stock.location.booking').search(cr, uid,[('location_id','=',location_id),('period_id','=',period_id),('state','=','done'),('service_category_id','=',service_categ_id)])
        can_book = True
        location = self.pool.get('stock.location').browse(cr, uid, [location_id])[0]

        if len(booking_ids) > 0:
           raise osv.except_osv(_('Warning'), _('You have selected Duplication Category')) 
        
        max_service_qty = self._get_max_service(cr, uid, location.id, service_categ_id)
        
        if len(booking_ids) == 0 and location and max_service_qty > len(max_ids):
        #elif len(booking_ids) == 0 and location and location.max_place_qty > len(max_ids):
            can_book = True
        else:
            can_book = False
            raise osv.except_osv(_('Warning'), _('You have Over max place can be sold ->'+location.name))            
        return can_book

    def create(self, cr, uid, vals, context=None):
        if 'sale_id' in vals and 'location_id' in vals:
            sale_obj = self.pool.get('sale.order').browse(cr, uid, vals['sale_id'])
            location_id = vals['location_id']
            customer_product_id = sale_obj.customer_product_id.id
            category_id = sale_obj.customer_product_id.categ_id.id
            period_id = False
            if sale_obj.sale_period_ids:
                period_id = sale_obj.sale_period_ids[0].period_id.id
            if sale_obj.service_product_id and period_id :
                service_category_id = sale_obj.service_product_id.categ_id.id
                can_book = self._can_booking(cr, uid, location_id, category_id, period_id, service_category_id )            
#            #vals.update({'sequence_id': self.create_sequence(cr, uid, vals, context)})
        return super(sale_branch_line, self).create(cr, uid, vals, context)
    
    def unlink(self, cr, uid, ids, context=None):
        #self._check_moves(cr, uid, ids, "unlink", context=context)
        for line in self.browse(cr, uid, ids, context):
            location_booking_ids = self.pool.get('stock.location.booking').search(cr, uid, [('order_id','=',line.sale_id.id),('location_id','=',line.location_id.id)])
            if location_booking_ids:
                self.pool.get('stock.location.booking').write(cr, uid, location_booking_ids, {'state':'cancel'})
        return super(sale_branch_line, self).unlink(cr, uid, ids, context=context)
    

sale_branch_line()

#POP-003
def next_date(start_date, dayname, diff_day=2):
    current = start_date - timedelta(days = diff_day)
    weekday = current.weekday()
    while current.weekday() <> dayname:
        current = current - timedelta(days = 1)
    return current

class sale_order(osv.osv):

    def schedule_manual_invoice(self, cr, uid, context=None):
        if context is None:
            context = {}
        cr.execute("""
            select id from sale_order 
            where  
              state = 'manual' 
              and client_order_ref is not null
              and date_period_start <= CURRENT_DATE 
              and date_period_finish >= CURRENT_DATE
        """)
        sale_ids = map(itemgetter(0), cr.fetchall())
        if sale_ids:
            for sale in self.pool.get('sale.order').browse(cr, uid, sale_ids):
                sale.manual_invoice()
        

    def _get_date_count(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        daycount = 0
        for line in self.browse(cr, uid, ids, context=context):
            for period in line.sale_period_ids:
                #POP-008, POP-020
                if period.period_id:
                    daycount = daycount + period.period_id.date_total
            res[line.id] = daycount
        return res
    #POP-012
    def _get_date_price(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        daycount = 0
        for line in self.browse(cr, uid, ids, context=context):
            for period in line.sale_period_ids:
                #POP-008, POP-020
                if period.period_id:
                    daycount = daycount + period.period_id.date_length
            res[line.id] = daycount
        return res

    def _get_branch_count(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        count = 0
        for line in self.browse(cr, uid, ids, context=context):
            for branch in line.sale_location_ids:
                count = count + 1
            res[line.id] = count
        return res

    def _get_period_count(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        count = 0
        for line in self.browse(cr, uid, ids, context=context):
            for branch in line.sale_period_ids:
                count = count + 1
            res[line.id] = count
        return res

    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        total_day = 1
        if line.with_period and line.order_id.sale_period_days:
            total_day = line.order_id.sale_period_days or 1.0

        total_location = 1
        if line.with_branch and line.order_id.sale_location_counts:
            total_location = line.order_id.sale_location_counts or 1.0

        price = line.price_unit * int(total_day) * int(total_location) * (1 - (line.discount or 0.0) / 100.0)

        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, price * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _period_date_start(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        date_start = None
        for line in self.browse(cr, uid, ids, context=context):
            for period in line.sale_period_ids:
                if not date_start:
                    date_start = period.period_id.date_start
                date_start = min(date_start, period.period_id.date_start)
            res[line.id] = date_start
        return res

    def _period_date_finish(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        date_finish = None
        for line in self.browse(cr, uid, ids, context=context):
            for period in line.sale_period_ids:
                date_finish = max(date_finish, period.period_id.date_finish)
            res[line.id] = date_finish
        return res
    
#DAY-007    
    def set_amount_mat(self, cr, uid, ids, context=None):
        res = {}        
        for order in self.browse(cr, uid, ids, context):
            location_mat_ids = self.pool.get('sale.cash.advance.material.line').search(cr, uid, [('sale_id','=',order.id)])
            if order.amount_by_store:
                if location_mat_ids:
                    self.pool.get('sale.cash.advance.material.line').write(cr, uid, location_mat_ids, {'amount': order.amount_by_store })
        return res  
#DAY-007    
    def _amount_mats(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        mats_val = 0.0
        oth_val = 0.0
        for line in self.browse(cr, uid, ids, context=context):
            for mats in line.sale_cash_advance_mat_ids:
                if mats.id:
                    mats_val = mats_val + mats.amount
            for oths in line.sale_cash_advance_ids:
                if oths.id:
                    oth_val = oth_val + oths.amount
            res[line.id] = mats_val + oth_val
        return res    
    #define how to convert delivery
    def choose_delivery_qty(self, cr, uid, ids, current, value_a, value_b, context=None):
        delivery = {}
        get_back = current - max(value_a, value_b)
        get_add = 0
        if get_back < 0:
            get_add = value_b - value_a
            if get_add < 0:
                get_back = abs(get_add)
                get_add = 0
            else:
                get_back = 0
        delivery = {'add':get_add,'back':get_back}
        return delivery
    
    _name = "sale.order"
    _inherit = "sale.order"

    _description = "Extended sale period for Sales Order"

    _columns = {
#DAY-003        
        'sale_cash_advance_ids':fields.one2many('sale.cash.advance.other.line','sale_id','Others Cash Advance Lines'),
#DAY-007
        'sale_cash_advance_mat_ids':fields.one2many('sale.cash.advance.material.line','sale_id','Material Cash Advance Lines'),        
        'amount_by_store': fields.float('Amount by Store'),
        'total_cash_advance': fields.function(_amount_mats, method=True, type='float', string='Total Cash Advance'),    
        'sale_period_ids': fields.one2many('sale.period.line', 'sale_id', 'Period Lines'),
        'sale_location_ids': fields.one2many('sale.branch.line', 'sale_id', 'Location Lines'),
        'sale_quotation_ids': fields.one2many('sale.order.quotation.line', 'saleorder_id', 'Quotation Manual'),
        'notes_quotation':fields.text("Quotation Notes"),
        'sale_period_days': fields.function(_get_date_count, method=True, type='integer', string='Summay Days'),
        'sale_location_counts': fields.function(_get_branch_count, method=True, type='integer', string='Summay Branchs'),
        'sale_period_counts': fields.function(_get_period_count, method=True, type='integer', string='Summay Periods'),

        'amount_untaxed': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax."),
        'amount_tax': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Taxes',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Total',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),

        'customer_product_id': fields.many2one('product.product', 'Customer Product', ondelete="restrict" ),
        'period_date_start': fields.function(_period_date_start, method=True, type='date', string='Start'),
        'period_date_finish': fields.function(_period_date_finish, method=True, type='date', string='Finish'),
        'date_period_start': fields.date('Start'),
        'date_period_finish': fields.date('Finish'),        
        'service_product_id': fields.many2one('product.product','Service Category'),
        'item_sale_check_ids': fields.many2many('product.product', 'product_product_sale_check_rel', 'sale_id', 'product_tmpl_id', 'Item Check Sales'),
        #POP-012
        'price_period_days': fields.function(_get_date_price, method=True, type='integer', string='Summay Price Days'),
        #POP-014
        'force_draft_state': fields.boolean('Force Draft State'),
        'force_equipment': fields.boolean('Force Equipment'),
        #POP-018
        'period_id': fields.many2one('omg.sale.period', 'Period ID'),
        #POP-027
    }

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            date_start = None
            date_finish = None
            period_id = False
            for period in line.sale_period_ids:
                if not date_start:
                    date_start = period.date_start
                if not period_id:
                    period_id = period.period_id.id
                date_finish = period.date_finish
            vals.update({'date_period_start': date_start,'date_period_finish': date_finish, 'period_id': period_id})
                                    
        return super(sale_order, self).write(cr, uid, ids, vals, context=context)

    def check_delivery_qty(self, cr, uid, ids, location_dest_id, period_id, product_id, days, context=None):
        period_obj = self.pool.get('omg.sale.period').browse(cr, uid, period_id)
        sql = '''
            select 
            --  product_id, 
            --  stock_move.period_id, 
            --  stock_move.location_dest_id,
              sum(stock_move.product_qty) as qty
            --  omg_sale_period.date_start,
            --  omg_sale_period.date_finish
            from stock_move 
            join stock_picking on stock_move.picking_id = stock_picking.id
            join omg_sale_period on stock_move.period_id = omg_sale_period.id
            where 
              stock_picking.type = 'out' and 
              date_finish <  to_date('%s', 'yyyy-mm-dd') and                              --current date of period
              date_finish >= to_date('%s', 'yyyy-mm-dd') - cast('%s days' as interval) and --period date 14 days ago
              stock_move.product_id = %s and                              --product_id
              stock_move.location_dest_id = %s and                       --location_dest_id
              stock_move.state <> 'cancel'
        '''
        cr.execute(sql % (
                    period_obj.date_start, 
                    period_obj.date_start,
                    days,product_id,location_dest_id))
        dict1 = cr.dictfetchall()
        current = 0
        if dict1:
            for data in dict1:
                current = data['qty'] or 0
        else:
            current = 0
        return current

    def _make_invoice(self, cr, uid, order, lines, context=None):
        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        obj_invoice_line = self.pool.get('account.invoice.line')
        if context is None:
            context = {}

        journal_ids = journal_obj.search(cr, uid, [('type', '=', 'sale'), ('company_id', '=', order.company_id.id)], limit=1)
        if not journal_ids:
            raise osv.except_osv(_('Error !'),
                _('There is no sales journal defined for this company: "%s" (id:%d)') % (order.company_id.name, order.company_id.id))
        a = order.partner_id.property_account_receivable.id
        pay_term = order.payment_term and order.payment_term.id or False
        invoiced_sale_line_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', order.id), ('invoiced', '=', True)], context=context)
        from_line_invoice_ids = []
        for invoiced_sale_line_id in self.pool.get('sale.order.line').browse(cr, uid, invoiced_sale_line_ids, context=context):
            for invoice_line_id in invoiced_sale_line_id.invoice_lines:
                if invoice_line_id.invoice_id.id not in from_line_invoice_ids:
                    from_line_invoice_ids.append(invoice_line_id.invoice_id.id)
        for preinv in order.invoice_ids:
            if preinv.state not in ('cancel',) and preinv.id not in from_line_invoice_ids:
                for preline in preinv.invoice_line:
                    inv_line_id = obj_invoice_line.copy(cr, uid, preline.id, {'invoice_id': False, 'price_unit': -preline.price_unit})
                    lines.append(inv_line_id)
        currency_ids = self.pool.get('res.currency').search(cr, uid, [('name','=','THB')])
        if currency_ids:
            currency_obj = self.pool.get('res.currency').browse(cr, uid, currency_ids)[0]
        currency_id = currency_obj.id
 #DAY-002        
        if lines:
            invoice_lines = {}
            invoice_line_dir = {}
            liness = []
            for j in range(len(lines)):
                account_invoice_lines = self.pool.get('account.invoice.line').browse(cr, uid, lines[j], context=context)
                invoice_lines = {'product_id': account_invoice_lines.product_id,
                                 'price_unit': account_invoice_lines.price_unit,
                                 'quantity': account_invoice_lines.quantity,
                                 'price_subtotal': account_invoice_lines.price_subtotal }
                invoice_line_dir[j] = invoice_lines
                for i in range(j):
                    if invoice_line_dir[i]['product_id'] == invoice_line_dir[j]['product_id'] and invoice_line_dir[i]['price_unit'] == invoice_line_dir[j]['price_unit']:
                        data = { 'quantity' : (invoice_line_dir[i]['quantity'] + invoice_line_dir[j]['quantity']),
                                 'price_subtotal':(invoice_line_dir[i]['price_subtotal'] + invoice_line_dir[j]['price_subtotal']) }
                        obj_invoice_line.write(cr,uid,lines[i],data,context=context)
                        liness.append(lines[j])
            lines = list(set(lines) - set(liness))                                         
                        
        inv = {
            'name': order.client_order_ref or '',
            'origin': order.name,
            'type': 'out_invoice',
            'reference': order.client_order_ref or order.name,
            'account_id': a,
            'partner_id': order.partner_id.id,
            'journal_id': journal_ids[0],
            'address_invoice_id': order.partner_invoice_id.id,
            'address_contact_id': order.partner_order_id.id,
            'invoice_line': [(6, 0, lines)],
            'currency_id': currency_id,
            'comment': order.note,
            'payment_term': pay_term,
            'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
            'date_invoice': time.strftime('%Y-%m-%d'),
            'company_id': order.company_id.id,
            'user_id': order.user_id and order.user_id.id or False
        }
        inv.update(self._inv_get(cr, uid, order))
        inv_id = inv_obj.create(cr, uid, inv, context=context)
        data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], pay_term, time.strftime('%Y-%m-%d'))
        if data.get('value', False):
            inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        return inv_id

    #POP-015
    def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done', 'exception'], date_inv = False, context=None):
        res = False
        invoices = {}
        invoice_ids = []
        picking_obj = self.pool.get('stock.picking')
        invoice = self.pool.get('account.invoice')
        obj_sale_order_line = self.pool.get('sale.order.line')
        if context is None:
            context = {}
        # If date was specified, use it as date invoiced, usefull when invoices are generated this month and put the
        # last day of the last month as invoice date
        if date_inv:
            context['date_inv'] = date_inv
        for o in self.browse(cr, uid, ids, context=context):
            lines = []
            for line in o.order_line:
                if line.invoiced:
                    continue
                elif (line.state in states) and (line.price_subtotal > 0):
                    lines.append(line.id)
            created_lines = obj_sale_order_line.invoice_line_create(cr, uid, lines)
            if created_lines:
                invoices.setdefault(o.partner_id.id, []).append((o, created_lines))
        if not invoices:
            for o in self.browse(cr, uid, ids, context=context):
                for i in o.invoice_ids:
                    if i.state == 'draft':
                        return i.id
        for val in invoices.values():
            if grouped:
                res = self._make_invoice(cr, uid, val[0][0], reduce(lambda x, y: x + y, [l for o, l in val], []), context=context)
                invoice_ref = ''
                for o, l in val:
                    invoice_ref += o.name + '|'
                    self.write(cr, uid, [o.id], {'state': 'progress'})
                    if o.order_policy == 'picking':
                        picking_obj.write(cr, uid, map(lambda x: x.id, o.picking_ids), {'invoice_state': 'invoiced'})
                    cr.execute('insert into sale_order_invoice_rel (order_id,invoice_id) values (%s,%s)', (o.id, res))
                invoice.write(cr, uid, [res], {'origin': invoice_ref, 'name': invoice_ref})
            else:
                for order, il in val:
                    res = self._make_invoice(cr, uid, order, il, context=context)
                    invoice_ids.append(res)
                    self.write(cr, uid, [order.id], {'state': 'progress'})
                    if order.order_policy == 'picking':
                        picking_obj.write(cr, uid, map(lambda x: x.id, order.picking_ids), {'invoice_state': 'invoiced'})
                    cr.execute('insert into sale_order_invoice_rel (order_id,invoice_id) values (%s,%s)', (order.id, res))
        return res
    
    #POP-024
    def _get_stock_store(self, cr, uid, product_id, location_id, quantity, equipment, context=None):
        stock_qty = 0.0
        if equipment:
            store_ids = self.pool.get('ineco.stock.location.inventory').search(cr, uid, [('product_id','=',product_id),('location_id','=',location_id),('quantity','>',0)] )
            if store_ids:
                store_inv = self.pool.get('ineco.stock.location.inventory').browse(cr, uid, store_ids)[0]
                stock_qty = min(quantity, store_inv.quantity) or 0.0
                store_inv.write({'quantity': store_inv.quantity - stock_qty})
        return stock_qty

    #POP-024
    def _get_stock_store_return(self, cr, uid, product_id, location_id, quantity, equipment, context=None):
        stock_qty = 0.0
        if equipment:
            store_ids = self.pool.get('ineco.stock.location.inventory').search(cr, uid, [('product_id','=',product_id),('location_id','=',location_id)] )
            if store_ids:
                store_inv = self.pool.get('ineco.stock.location.inventory').browse(cr, uid, store_ids)[0]
                stock_qty = quantity
                store_inv.write({'quantity': store_inv.quantity + stock_qty})
        return stock_qty

    def action_ship_create(self, cr, uid, ids, *args):
        wf_service = netsvc.LocalService("workflow")
        picking_id = False
        move_obj = self.pool.get('stock.move')
        proc_obj = self.pool.get('procurement.order')
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        #change this : for OMG HOLDING
        for order in self.browse(cr, uid, ids, context={}):
            if not (order.sale_period_ids and order.sale_location_ids):
                proc_ids = []
                output_id = order.shop_id.warehouse_id.lot_output_id.id
                picking_id = False
                for line in order.order_line:
                    proc_id = False
                    date_planned = datetime.now() + relativedelta(days=line.delay or 0.0)
                    date_planned = (date_planned - timedelta(days=company.security_lead)).strftime('%Y-%m-%d %H:%M:%S')
    
                    if line.state == 'done':
                        continue
                    move_id = False
                    if line.product_id and line.product_id.product_tmpl_id.type in ('product', 'consu'):
                        location_id = order.shop_id.warehouse_id.lot_stock_id.id
                        if not picking_id:
                            pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
                            picking_id = self.pool.get('stock.picking').create(cr, uid, {
                                'name': pick_name,
                                'origin': order.name,
                                'type': 'out',
                                'state': 'auto',
                                'move_type': order.picking_policy,
                                'sale_id': order.id,
                                'address_id': order.partner_shipping_id.id,
                                'note': order.note,
                                'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
                                'company_id': order.company_id.id,
                                'customer_id': order.partner_id.id,
                            })
                        
                        move_id = self.pool.get('stock.move').create(cr, uid, {
                            'name': line.name[:64],
                            'picking_id': picking_id,
                            'product_id': line.product_id.id,
                            'date': date_planned,
                            'date_expected': order.date_period_start, #date_planned,
                            'product_qty': line.product_uom_qty,
                            'product_uom': line.product_uom.id,
                            'product_uos_qty': line.product_uos_qty,
                            'product_uos': (line.product_uos and line.product_uos.id)\
                                    or line.product_uom.id,
                            'product_packaging': line.product_packaging.id,
                            'address_id': line.address_allotment_id.id or order.partner_shipping_id.id,
                            'location_id': location_id,
                            'location_dest_id': output_id,
                            'sale_line_id': line.id,
                            'tracking_id': False,
                            'state': 'draft',
                            #'state': 'waiting',
                            'note': line.notes,
                            'company_id': order.company_id.id,
                        })
    
                    if line.product_id:
                        proc_id = self.pool.get('procurement.order').create(cr, uid, {
                            'name': line.name,
                            'origin': order.name,
                            'date_planned': date_planned,
                            'product_id': line.product_id.id,
                            'product_qty': line.product_uom_qty,
                            'product_uom': line.product_uom.id,
                            'product_uos_qty': (line.product_uos and line.product_uos_qty)\
                                    or line.product_uom_qty,
                            'product_uos': (line.product_uos and line.product_uos.id)\
                                    or line.product_uom.id,
                            'location_id': order.shop_id.warehouse_id.lot_stock_id.id,
                            'procure_method': line.type,
                            'move_id': move_id,
                            'property_ids': [(6, 0, [x.id for x in line.property_ids])],
                            'company_id': order.company_id.id,
                        })
                        proc_ids.append(proc_id)
                        self.pool.get('sale.order.line').write(cr, uid, [line.id], {'procurement_id': proc_id})
                        if order.state == 'shipping_except':
                            for pick in order.picking_ids:
                                for move in pick.move_lines:
                                    if move.state == 'cancel':
                                        mov_ids = move_obj.search(cr, uid, [('state', '=', 'cancel'),('sale_line_id', '=', line.id),('picking_id', '=', pick.id)])
                                        if mov_ids:
                                            for mov in move_obj.browse(cr, uid, mov_ids):
                                                move_obj.write(cr, uid, [move_id], {'product_qty': mov.product_qty, 'product_uos_qty': mov.product_uos_qty})
                                                proc_obj.write(cr, uid, [proc_id], {'product_qty': mov.product_qty, 'product_uos_qty': mov.product_uos_qty})
    
                val = {}
    
                if picking_id:
                    wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
    
                for proc_id in proc_ids:
                    wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)
    
                if order.state == 'shipping_except':
                    val['state'] = 'progress'
                    val['shipped'] = False
    
                    if (order.order_policy == 'manual'):
                        for line in order.order_line:
                            if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                                val['state'] = 'manual'
                                break
                self.write(cr, uid, [order.id], val)
            else: #this is change
                for period in order.sale_period_ids:
                    t0 = datetime.now()
                    #print "Start Period %s %s" % ('OK', datetime.now() - t0)
                    if period.period_id.warehouse_lock:
                        raise osv.except_osv(_('Period Locked.'), _('Peiord ('+ period.period_id.name +') was locked by Logistic Control.'))
                    for location in order.sale_location_ids:      
                        #print "Location %s %s" % (location.location_id.name, datetime.now()-t0)                  
                        proc_ids = []
                        output_id = order.shop_id.warehouse_id.lot_output_id.id
                        picking_id = False
                        for line in order.order_line:
                            #print "Location %s -> %s %s" % (location.location_id.name, line.product_id.name, datetime.now()-t0)
                            proc_id = False
                            date_planned = datetime.strptime(period.date_start, '%Y-%m-%d')
                            #date_planned = datetime.strptime(period.date_start, '%Y-%m-%d') - relativedelta(days=line.delay or 0.0) - relativedelta(days=location.location_id.chained_delay or 0.0)
                            #date_planned = (date_planned - timedelta(days=company.security_lead)).strftime('%Y-%m-%d %H:%M:%S')
                            date_arrival = (datetime.strptime(period.date_start, '%Y-%m-%d') - relativedelta(days=7 or 0.0)).strftime('%Y-%m-%d')
            
                            if line.state == 'done':
                                continue
                            move_id = False
                            new_qty = 0
                            if line.product_id and line.product_id.product_tmpl_id.type in ('product', 'consu'):
                                #POP-019
                                new_product_ids = self.pool.get('ineco.stock.location.product.mapping').search(cr, uid, [('location_id','=',location.location_id.id),('product_id_from','=',line.product_id.id)])
                                new_product_id = line.product_id
                                if new_product_ids:
                                    new_product_id = self.pool.get('ineco.stock.location.product.mapping').browse(cr, uid, new_product_ids)[0].product_id_to
                                location_id = order.shop_id.warehouse_id.lot_stock_id.id
                                if not picking_id:
                                    oaname = ""
                                    oamobile = ""
                                    sms_text = ""
                                    if order.partner_id.sms_type:
                                        condition = order.partner_id.sms_type.condition
                                        location_sql = """
                                            select 
                                              res_partner_address.name, 
                                              res_partner_address.mobile
                                            from stock_oa_address
                                            join res_partner_address on stock_oa_address.address_id = res_partner_address.id
                                            join res_partner_title on res_partner_address.title = res_partner_title.id
                                            where location_id = %s 
                                              and res_partner_title.name = '%s' 
                                              and res_partner_address.type = 'contact'
                                          """
                                        cr.execute(location_sql % (location.location_id.id, condition))
                                        dict1 = cr.dictfetchall()
                                        for row in dict1:
                                            if not oaname:
                                                oaname = row["name"] or ""
                                            if not oamobile:
                                                oamobile = row["mobile"] or ""
                                    if order.partner_id.sms_text:
                                        sms_text = order.partner_id.sms_text or ""
                                    #else:
                                    #    if location.location_id.oa_address_ids:
                                    #        oaname = location.location_id.oa_address_ids[0].address_id.name
                                    #    if location.location_id.oa_address_ids:
                                    #        oamobile = location.location_id.oa_address_ids[0].address_id.phone
                                    
                                    #POP-003
                                    if location.location_id.ineco_logistic_path.delivery_day:
                                        day_name_delivery = int(location.location_id.ineco_logistic_path.delivery_day) 
                                    else: 
                                        day_name_delivery = datetime.strptime(period.date_start, '%Y-%m-%d').weekday()
                                    if location.location_id.ineco_logistic_path.arrival_day:
                                        day_name_arrival = int(location.location_id.ineco_logistic_path.arrival_day) 
                                    else:
                                        day_name_arrival = datetime.strptime(period.date_start, '%Y-%m-%d').weekday()
                                        
                                    date_period_start = datetime.strptime(period.date_start, '%Y-%m-%d')
                                    
                                    date_arrival2 = next_date(date_period_start, day_name_arrival, 2 )
                                    date_delivery2 = next_date(date_arrival2, day_name_delivery, 1 )
                                    
                                    pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
                                    picking_id = self.pool.get('stock.picking').create(cr, uid, {
                                        'name': pick_name,
                                        'origin': order.name,
                                        'type': 'out',
                                        'state': 'draft',
                                        'move_type': order.picking_policy,
                                        'sale_id': order.id,
                                        'address_id': location.location_id.address_id.id or "",
                                        'oa_contact_name': oaname or "",
                                        'oa_mobile_no': oamobile or "",
                                        'note': order.note,
                                        'invoice_state': '2binvoiced',
                                        'company_id': order.company_id.id,
                                        'period_id': period.period_id.id,
                                        'customer_product_id': order.customer_product_id.id,
                                        'customer_id': order.partner_id.id,
                                        #POP-003
                                        'date_arrival': date_arrival2 or date_arrival,
                                        #POP-013
                                        #'ineco_delivery_date': date_delivery2 or False,
                                        'path': location.location_id.path,
                                        'location_store_id': location.location_id.id,
                                        'sms_text': sms_text,
                                        #POP-002 Add Logistic Path
                                        'ineco_logistic_path': location.location_id.ineco_logistic_path.id,
                                    })                                    
                                #change quantity
                                val = 0.0
                                total_day = 1
                                if line.with_period and line.order_id.sale_period_days:
                                    total_day = line.order_id.sale_period_days or 1.0
                        
                                total_location = 1
                                if line.with_branch and line.order_id.sale_location_counts:
                                    total_location = line.order_id.sale_location_counts or 1.0
                        
                                new_qty = int(total_day) * line.product_uom_qty
                                
                                #POP-005
                                if not line.apply_all_store:
                                    #POP-011
                                    if location.estimate:
                                        estimate = location.estimate           
                                        new_qty = ((estimate * (1/(line.omg_ratio or 1.0))) / (line.omg_sampling or 1.0)) * int(total_day)                                
                                        new_qty = round(new_qty)
                                        if line.omg_percent_rate:
                                            new_qty = ( ( estimate * line.omg_percent_rate/100 ) / (line.omg_ratio or 1.0) ) * int(total_day)
                                            new_qty = round(new_qty)                                            
                                    else:
                                        lineqty_obj = self.pool.get('stock.location.line.qty')
                                        lineqty_ids = lineqty_obj.search(cr, uid, [('location_id', '=', location.location_id.id),('categ_id','=',line.product_id.categ_id.id)])
                                        if lineqty_ids:
                                            if line.product_id.use_location_qty:
                                                lineqty = lineqty_obj.browse(cr, uid, lineqty_ids)[0]           
                                                #POP-007                 
                                                new_qty = ((lineqty.quantity * (1/(line.omg_ratio or 1.0))) / (line.omg_sampling or 1.0)) * int(total_day)
                                                #POP-009
                                                new_qty = round(new_qty)
                                        else:
                                            if line.product_id.customer_material:
                                                raise osv.except_osv(_('No Product Estimate'), _('Please define product ('+ line.product_id.name +') estimate in location \n'+location.location_id.name+' | '+line.product_id.categ_id.name+'.'))                                        
                                            else:
                                                #POP-007
                                                new_qty = ((line.product_uom_qty * (1/(line.omg_ratio or 1.0))) / (line.omg_sampling or 1.0)) * int(total_day)
                                                #POP-009
                                                new_qty = round(new_qty)
                                    #POP-023
                                    #DAY-001 ต่ำกว่า 0.25 = 0 , 0.25-0.75 = 0.5 , 0.76+ = 1
                                    if line.product_id.uom_id <> line.product_id.warehouse_uom and line.product_id.full_warehouse_uom:
                                        full_warehouse_qty = round(1/(line.product_id.warehouse_uom.factor or 1))
                                        if full_warehouse_qty > 1:
                                            lesspack = round(new_qty,2) % round(full_warehouse_qty,2)
                                            fullpack = round(new_qty,2) / round(full_warehouse_qty,2)
                                            if fullpack:
                                                if fullpack > 1:
                                                    #fullpack = round(fullpack)
                                                    fullpack = round(new_qty,2) // round(full_warehouse_qty,2)
                                                    less_ratio = lesspack / full_warehouse_qty
                                                    if less_ratio and less_ratio >= 0.75:
                                                        fullpack = fullpack + 1
                                                        new_qty = fullpack * full_warehouse_qty
                                                    elif less_ratio and less_ratio >= 0.25:
                                                        fullpack = fullpack + 0.5
                                                        new_qty = round(fullpack * full_warehouse_qty)
                                                    else:
                                                        new_qty = fullpack * full_warehouse_qty
                                                else:
                                                    new_qty = new_qty
                                            else:
                                                new_qty = new_qty
        
                                                #old code new_qty = lineqty.quantity * int(total_day)
                                
                                #only bom process -> delivery
                                if line.product_id.procure_method == 'make_to_order' and line.product_id.supply_method == 'produce':
                                    new_qty = line.product_uom_qty
                                
                                
                                if new_qty <> 0:                               
                                    new_back = 0
                                    #Disable Warehouse Compute Equipment Delivery Method by Warehouse (P'Aah)
                                    #if line.product_id.equipment:
                                    #    current = self.check_delivery_qty(
                                    #                cr,
                                    #                uid,
                                    #                ids,
                                    #                location.location_id.id, 
                                    #                period.period_id.id, 
                                    #                line.product_id.id, 
                                    #                21)
                                    #    value_a = self.check_delivery_qty( 
                                    #                cr,
                                    #                uid,
                                    #                ids,
                                    #                location.location_id.id, 
                                    #                period.period_id.id, 
                                    #                line.product_id.id, 
                                    #                14)
                                    #    value_b = new_qty
                                    #    new_qty = self.choose_delivery_qty(cr, uid, ids, current, value_a, value_b)['add']
                                    #    new_back = self.choose_delivery_qty(cr, uid, ids, current, value_a, value_b)['back']

                                    #POP-017
                                    move_id = False
                                    if not (not location.location_id.omg_alway_equipment and line.product_id.equipment) or order.force_equipment :
                                        #Excute BOM Process
                                        bom_ids = self.pool.get('mrp.bom').search(cr, uid, [('bom_id','=',False),('product_id','=',new_product_id.id)])
                                        if not bom_ids:
                                            move_id = self.pool.get('stock.move').create(cr, uid, {
                                                'name': line.name[:64],
                                                'picking_id': picking_id,
                                                #POP-019
                                                #'product_id': line.product_id.id,
                                                'product_id': new_product_id.id,
                                                'date': date_planned,
                                                'date_expected': date_planned,
                                                'product_qty': new_qty,
                                                'product_uom': line.product_uom.id,
                                                'product_uos_qty': new_qty,
                                                'product_uos': (line.product_uos and line.product_uos.id)\
                                                        or line.product_uom.id,
                                                'product_packaging': line.product_packaging.id,
                                                'address_id': location.location_id.address_id.id,
                                                'location_id': location_id,
                                                'location_dest_id': location.location_id.id,
                                                'sale_line_id': line.id,
                                                'tracking_id': False,
                                                'state': 'draft',
                                                #'state': 'waiting',
                                                'note': line.notes,
                                                'company_id': order.company_id.id,
                                                'period_id': period.period_id.id,
                                                'customer_product_id': order.customer_product_id.id,
                                                #POP-022
                                                'price_unit': line.price_unit or 0,
                                                #POP-024
                                                'store_qty': self._get_stock_store(cr, uid, new_product_id.id, location.location_id.id, new_qty, new_product_id.equipment or False  ),
                                            })
                                        else:
                                            for boms in self.pool.get('mrp.bom').browse(cr, uid, bom_ids):
                                                for bom in boms.bom_lines:
                                                    move_id = self.pool.get('stock.move').create(cr, uid, {
                                                        'name': line.name[:64],
                                                        'picking_id': picking_id,
                                                        #POP-019
                                                        #'product_id': line.product_id.id,
                                                        'product_id': bom.product_id.id,
                                                        'date': date_planned,
                                                        'date_expected': date_planned,
                                                        'product_qty': new_qty * bom.product_qty,
                                                        'product_uom': bom.product_id.uom_id.id,
                                                        'product_uos_qty': new_qty * bom.product_qty,
                                                        'product_uos': bom.product_id.uom_id.id,
                                                        'product_packaging': line.product_packaging.id,
                                                        'address_id': location.location_id.address_id.id,
                                                        'location_id': location_id,
                                                        'location_dest_id': location.location_id.id,
                                                        'sale_line_id': line.id,
                                                        'tracking_id': False,
                                                        'state': 'draft',
                                                        #'state': 'waiting',
                                                        'note': line.notes,
                                                        'company_id': order.company_id.id,
                                                        'period_id': period.period_id.id,
                                                        'customer_product_id': order.customer_product_id.id,
                                                        #POP-022
                                                        'price_unit': line.price_unit or 0,
                                                        #POP-024
                                                        'store_qty': self._get_stock_store(cr, uid, bom.product_id.id, location.location_id.id, new_qty * bom.product_qty, bom.product_id.equipment or False ),
                                                    })
                                            move_id = False    
                            #POP-017                            
                            #if line.product_id and new_qty <> 0 and move_id :
                            #    #print "Procurement Start --> %s %s" % (location.location_id.name, datetime.now()-t0)
                            #    proc_id = self.pool.get('procurement.order').create(cr, uid, {
                            #        'name': line.name,
                            #        'origin': order.name,
                            #        'date_planned': date_planned,
                            #        #'product_id': line.product_id.id,
                            #        #POP-019
                            #        'product_id': new_product_id.id,
                            #        'product_qty': new_qty,
                            #        'product_uom': line.product_uom.id,
                            #        'product_uos_qty': (line.product_uos and line.product_uos_qty)\
                            #                or new_qty,
                            #        'product_uos': (line.product_uos and line.product_uos.id)\
                            #                or line.product_uom.id,
                            #        'location_id': order.shop_id.warehouse_id.lot_stock_id.id,
                            #        'procure_method': line.type,
                            #        'move_id': move_id,
                            #        'property_ids': [(6, 0, [x.id for x in line.property_ids])],
                            #        'company_id': order.company_id.id,
                            #        'period_id': period.period_id.id,
                            #        'customer_product_id': order.customer_product_id.id,
                            #    })
                                
                            #    wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)
                                
                                #print "Procurement Finish --> %s %s" % (location.location_id.name, datetime.now()-t0)
                                #proc_ids.append(proc_id)
                                self.pool.get('sale.order.line').write(cr, uid, [line.id], {'procurement_id': proc_id})
                                if order.state == 'shipping_except':
                                    for pick in order.picking_ids:
                                        for move in pick.move_lines:
                                            if move.state == 'cancel':
                                                mov_ids = move_obj.search(cr, uid, [('state', '=', 'cancel'),('sale_line_id', '=', line.id),('picking_id', '=', pick.id)])
                                                if mov_ids:
                                                    for mov in move_obj.browse(cr, uid, mov_ids):
                                                        move_obj.write(cr, uid, [move_id], {'product_qty': new_qty, 'product_uos_qty': new_qty})
                                                        proc_obj.write(cr, uid, [proc_id], {'product_qty': new_qty, 'product_uos_qty': new_qty})
            
                        val = {}
                        
                        #print "Work Flow BOM Explore--> %s %s" % (location.location_id.name, datetime.now()-t0)
                        #if not order.force_draft_state:
                        #    if picking_id:
                        #        print "Picking Confirm Start --> %s %s" % (location.location_id.name, datetime.now()-t0)
                        #        wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
                        #        print "Picking Confirm Start --> %s %s" % (location.location_id.name, datetime.now()-t0)
            
                        #for proc_id in proc_ids:
                        #    wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)
                       
                        if order.state == 'shipping_except':
                            val['state'] = 'progress'
                            val['shipped'] = False
            
                            if (order.order_policy == 'manual'):
                                for line in order.order_line:
                                    if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                                        val['state'] = 'manual'
                                        break
                        #print "Write Sale Order --> %s %s" % (location.location_id.name, datetime.now()-t0)
                        self.write(cr, uid, [order.id], val)
                        
                        #POP-001 
                        #print "Create Stock Move --> %s %s" % (location.location_id.name, datetime.now()-t0)
                        #stock_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id','=',picking_id)])
                        #for stock_move_line in self.pool.get('stock.move').browse(cr, uid, stock_ids):
                        #    stock_move_line.write({'location_dest_id':location.location_id.id})
                        #POP-001                        

                #Create Request for Customer Material
                #03-11-11 By Tititab Srisookco
                #print "Start RFQ Customer Material %s " % (datetime.now() - t0)
                customer_material_sql = """
                    select 
                      sp.origin as order_no,
                      sp.customer_id, 
                      sp.customer_product_id, 
                      sp.period_id,
                      sm.product_id,
                      sm.product_uom, 
                      sum(sm.product_qty) as quantity
                    from stock_move sm
                    join stock_picking sp on sm.picking_id = sp.id
                    join product_product pp on sm.product_id = pp.id
                    where sp.type = 'out' 
                          and sm.state not in ('done','cancel') 
                          and pp.customer_material = True
                          and sp.origin = '%s'
                    group by
                      sp.origin,
                      sp.customer_id, 
                      sp.customer_product_id, 
                      sp.period_id,
                      sm.product_id,
                      sm.product_uom                """
                cr.execute(customer_material_sql % order.name)
                material_list = cr.dictfetchall()
                if material_list:
                    data =  self.browse(cr, uid, ids, context={})[0]
                    company = self.pool.get('res.users').browse(cr, uid, uid, context={}).company_id
                    order_obj = self.pool.get('purchase.order')
                    order_line_obj = self.pool.get('purchase.order.line')
                    partner_obj = self.pool.get('res.partner')
                    #tender_line_obj = self.pool.get('purchase.requisition.line')
                    pricelist_obj = self.pool.get('product.pricelist')
                    prod_obj = self.pool.get('product.product')
                    #tender_obj = self.pool.get('purchase.requisition')
                    acc_pos_obj = self.pool.get('account.fiscal.position')
                    partner_id = data.partner_id.id
                    supplier_data = data.partner_id
                    address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
                    list_line=[]
                    purchase_order_line={}
                    for res in material_list:
                    #create PO Lines                    
                    #for line in tender.line_ids:
                        product_id = self.pool.get('product.product').browse(cr, uid, res['product_id'])
                        product_qty = res['quantity']
                        partner_list = sorted([(partner.sequence, partner) for partner in  product_id.seller_ids if partner])
                        partner_rec = partner_list and partner_list[0] and partner_list[0][1] or False
                        uom_id = self.pool.get('product.uom').browse(cr, uid, res['product_uom'])
                        #uom_id = line.product_id.uom_po_id and line.product_id.uom_po_id.id or False
    
                        newdate = datetime.today()
                        delay = partner_rec and partner_rec.delay or 0.0
                        if delay:
                            newdate += relativedelta(days=delay)
    
                        partner = partner_rec and partner_rec.name or supplier_data
                        pricelist_id = partner.property_product_pricelist_purchase and partner.property_product_pricelist_purchase.id or False
                        price = 0
                        #price = pricelist_obj.price_get(cr, uid, [pricelist_id], product_id.id, product_qty, False, {'uom': uom_id})[pricelist_id]
                        product = prod_obj.browse(cr, uid, product_id.id, context={})
                        location_id =  partner.property_stock_customer.id
                        #location_id = self.pool.get('stock.warehouse').read(cr, uid, [tender.warehouse_id.id], ['lot_input_id'])[0]['lot_input_id'][0]
    
                        purchase_order_line= {
                                'name': product.partner_ref,
                                'product_qty': product_qty,
                                'product_id': product_id.id,
                                'product_uom': uom_id.id,
                                'price_unit': price,
                                'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
                                'notes': product.description_purchase,
                        }
                        taxes_ids = product_id.product_tmpl_id.supplier_taxes_id
                        taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)
                        purchase_order_line.update({
                                'taxes_id': [(6,0,taxes)]
                            })
                        list_line.append(purchase_order_line)
                    purchase_id = order_obj.create(cr, uid, {
                        'origin': order.name,
                        'partner_id': partner_id,
                        'partner_address_id': address_id,
                        'pricelist_id': pricelist_id,
                        'fiscal_position': partner.property_account_position and partner.property_account_position.id or False,
                        'requisition_id':False,
                        'notes': False,
                        'warehouse_id': data.shop_id.warehouse_id.id  ,
                        'location_id': data.shop_id.warehouse_id.lot_input_id.id,
                        'company_id':data.company_id.id,
                        'partner_ref': data.client_order_ref,
                        'invoice_method': 'manual',
                        'manage': True,
                        'type_omg': 'client',
                    })
                    order_ids=[]
                    for order_line in list_line:
                        order_line.update({
                                'order_id': purchase_id
                            })
                        order_line_obj.create(cr,uid,order_line)

                #Create Request for Cash Advance
                #03-11-11 By Tititab Srisookco
                print "Start Cash Advance %s " % (datetime.now() - t0)
                customer_material_sql = """
                    select 
                      sp.origin as order_no,
                      sp.customer_id, 
                      sp.customer_product_id, 
                      sp.period_id,
                      sm.product_id,
                      sm.product_uom, 
                      sum(sm.product_qty) as quantity,
                      sm.price_unit as price_unit
                    from stock_move sm
                    join stock_picking sp on sm.picking_id = sp.id
                    join product_product pp on sm.product_id = pp.id
                    where sp.type = 'out' 
                          and sm.state not in ('done','cancel') 
                          and pp.cash_advance = True
                          and sp.origin = '%s'
                    group by
                      sp.origin,
                      sp.customer_id, 
                      sp.customer_product_id, 
                      sp.period_id,
                      sm.product_id,
                      sm.price_unit,
                      sm.product_uom                """
                cr.execute(customer_material_sql % order.name)
                material_list = cr.dictfetchall()
                if material_list:
                    data =  self.browse(cr, uid, ids, context={})[0]
                    company = self.pool.get('res.users').browse(cr, uid, uid, context={}).company_id
                    order_obj = self.pool.get('purchase.order')
                    order_line_obj = self.pool.get('purchase.order.line')
                    partner_obj = self.pool.get('res.partner')
                    #tender_line_obj = self.pool.get('purchase.requisition.line')
                    pricelist_obj = self.pool.get('product.pricelist')
                    prod_obj = self.pool.get('product.product')
                    #tender_obj = self.pool.get('purchase.requisition')
                    acc_pos_obj = self.pool.get('account.fiscal.position')
                    partner_id = company.partner_id.id
                    supplier_data = data.partner_id
                    address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
                    list_line=[]
                    purchase_order_line={}
                    for res in material_list:
                    #create PO Lines                    
                    #for line in tender.line_ids:
                        product_id = self.pool.get('product.product').browse(cr, uid, res['product_id'])
                        product_qty = res['quantity']
                        partner_list = sorted([(partner.sequence, partner) for partner in  product_id.seller_ids if partner])
                        partner_rec = partner_list and partner_list[0] and partner_list[0][1] or False
                        uom_id = self.pool.get('product.uom').browse(cr, uid, res['product_uom'])
                        #uom_id = line.product_id.uom_po_id and line.product_id.uom_po_id.id or False
    
                        newdate = datetime.today()
                        delay = partner_rec and partner_rec.delay or 0.0
                        if delay:
                            newdate += relativedelta(days=delay)
    
                        partner = partner_rec and partner_rec.name or supplier_data
                        pricelist_id = partner.property_product_pricelist_purchase and partner.property_product_pricelist_purchase.id or False
                        #POP-022
                        price = res['price_unit'] or 0.0
                        #price = pricelist_obj.price_get(cr, uid, [pricelist_id], product_id.id, product_qty, False, {'uom': uom_id})[pricelist_id]
                        product = prod_obj.browse(cr, uid, product_id.id, context={})
                        location_id =  partner.property_stock_customer.id
                        #location_id = self.pool.get('stock.warehouse').read(cr, uid, [tender.warehouse_id.id], ['lot_input_id'])[0]['lot_input_id'][0]
    
                        purchase_order_line= {
                                'name': product.partner_ref,
                                'product_qty': product_qty,
                                'product_id': product_id.id,
                                'product_uom': uom_id.id,
                                'price_unit': price,
                                'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
                                'notes': product.description_purchase,
                        }
                        taxes_ids = product_id.product_tmpl_id.supplier_taxes_id
                        taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)
                        purchase_order_line.update({
                                'taxes_id': [(6,0,taxes)]
                            })
                        list_line.append(purchase_order_line)
                    purchase_id = order_obj.create(cr, uid, {
                        'origin': order.name,
                        'partner_id': partner_id,
                        'partner_address_id': address_id,
                        'pricelist_id': pricelist_id,
                        'fiscal_position': partner.property_account_position and partner.property_account_position.id or False,
                        'requisition_id':False,
                        'notes': False,
                        'warehouse_id': data.shop_id.warehouse_id.id  ,
                        'location_id': data.shop_id.warehouse_id.lot_input_id.id,
                        'company_id':data.company_id.id,
                        'partner_ref': data.client_order_ref,
                        'invoice_method': 'manual',
                        'manage': True,
                        'type_omg': 'cash',
                    })
                    order_ids=[]
                    for order_line in list_line:
                        order_line.update({
                                'order_id': purchase_id
                            })
                        order_line_obj.create(cr,uid,order_line)

                
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context):
            #POP-021
            if order.period_id.warehouse_lock:
                raise osv.except_osv(_('Period Locked.'), _('Peiord ('+ order.period_id.name +') was locked by Logistic Control.'))

            #DAY-004
#            for location_book in order.sale_location_ids:
#                location_booking_ids = self.pool.get('stock.location.booking').search(cr, uid, 
#                    [('order_id','=',location_book.sale_id.id),('location_id','=',location_book.location_id.id)])
#                if location_booking_ids:
#                    self.pool.get('stock.location.booking').write(cr, uid, location_booking_ids, {'state':'cancel'})

            for pick in order.picking_ids:
                if pick.state not in ('cancel'):
                    for line in pick.move_lines:
                        self._get_stock_store_return(cr, uid, line.product_id.id, line.location_dest_id.id, line.product_qty, line.product_id.equipment or False)
                        
        return super(sale_order, self).action_cancel(cr, uid, ids, context=context)

sale_order()

class sale_order_quotation_line(osv.osv):
    _name = 'sale.order.quotation.line'
    _description = 'Sales Manual Quotation Line'
    _columns = {
        'saleorder_id': fields.many2one('sale.order', 'Order Reference', required=True, ondelete='cascade', select=True),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], ondelete="restrict" ),
        'name': fields.char('Description', size=256, required=True, select=True ),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Sale Price')),
        'product_uom_qty': fields.float('Quantity (UoM)', digits=(16, 2), required=True ),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure ', required=True, ondelete="restrict" ),
    }
sale_order_quotation_line()

class sale_order_line(osv.osv):

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            total_day = 1
            if line.with_period and line.order_id.sale_period_days:
                #total_day = line.order_id.sale_period_days or 1.0
                #POP-012
                total_day = line.order_id.price_period_days or 1.0

            total_location = 1
            if line.with_branch and line.order_id.sale_location_counts:
                total_location = line.order_id.sale_location_counts or 1.0

            price = line.price_unit * int(total_day) * int(total_location) * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
            #print price, line.price_unit, int(total_day), int(total_location)
        return res

    def _get_sale_unitprice(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        sum_price = 0.0            
        for line in self.browse(cr, uid, ids, context=context):
            price_unit = self.pool.get('product.pricelist').price_get(cr, uid, [line.order_id.pricelist_id.id], line.product_id.id, 1.0, line.order_id.partner_id.id, {'date': line.order_id.date_order, 'uom': line.product_id.uom_id.id })[line.order_id.pricelist_id.id]            
            cur = line.order_id.pricelist_id.currency_id            
            res[line.id] = cur_obj.round(cr, uid, cur, price_unit)

            total_day = 1
            if line.with_period and line.order_id.sale_period_days:
                #total_day = line.order_id.sale_period_days or 1.0
                #POP-012
                total_day = line.order_id.price_period_days or 1.0  
            total_location = 1
            if line.with_branch and line.order_id.sale_location_counts:
                total_location = line.order_id.sale_location_counts or 1.0
            sum_price = int(total_day) * price_unit * int(total_location)
            res[line.id] = sum_price 
            #self.pool.get('sale.order.line').write(cr, uid, ids, {'price_unit':sum_price})        
        return res

    def _get_total_period(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        count = 0
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = int(line.order_id.sale_period_days)
        return res

    def _get_total_branch(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        count = 0
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = int(line.order_id.sale_location_counts)
        return res

    _name = "sale.order.line"
    _inherit = "sale.order.line"
    _description="Extension of Sale Order for OMG Thailand Co.,Ltd."
    _columns = {
        'price_subtotal': fields.function(_amount_line, method=True, string='Subtotal', digits_compute= dp.get_precision('Sale Price')),
        'with_branch': fields.boolean('With Branch'),
        'with_period': fields.boolean('With Period'),
        'sale_subtotal': fields.function(_get_sale_unitprice, method=True, string='Sale Unit Price'),
        'total_period': fields.function(_get_total_period, method=True, string='Total Periods'),
        'total_branch': fields.function(_get_total_branch, method=True, string='Total Branchs'),
        'uom_category_id': fields.many2one('product.uom.categ', 'UOM Category', ondelete="restrict"),
        'apply_all_store': fields.boolean('Apply All Store'),
        'omg_ratio': fields.float('Ratio', digits=(8,2)),
        'omg_sampling': fields.integer('Qty Sampling'),
        'omg_percent_rate': fields.integer('% Rate'),
        'branch_ids': fields.one2many('sale.order.line.branch', 'sale_line_id', 'Branch')
    }
    _defaults = {
        'with_branch':True,
        'with_period':False,
        'omg_ratio': 1.0,
        'omg_sampling': 1.0,
        'omg_percent_rate': 0,
    }
    
    #POP-025
    def create_line_branch(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids):
            cr.execute('delete from sale_order_line_branch where sale_line_id = %s' % (line.id))
            cr.commit()
            
            total_day = 1
            if line.with_period and line.order_id.sale_period_days:
                total_day = line.order_id.sale_period_days or 1.0
    
            total_location = 1
            if line.with_branch and line.order_id.sale_location_counts:
                total_location = line.order_id.sale_location_counts or 1.0
    
            new_qty = int(total_day) * line.product_uom_qty
            
            #POP-005
            if not line.apply_all_store:
                #POP-011
                if location.estimate:
                    estimate = location.estimate           
                    new_qty = ((estimate * (1/(line.omg_ratio or 1.0))) / (line.omg_sampling or 1.0)) * int(total_day)                                
                    new_qty = round(new_qty)
                    if line.omg_percent_rate:
                        new_qty = ( ( estimate * line.omg_percent_rate/100 ) / (line.omg_ratio or 1.0) ) * int(total_day)
                        new_qty = round(new_qty)                                            
                else:
                    lineqty_obj = self.pool.get('stock.location.line.qty')
                    lineqty_ids = lineqty_obj.search(cr, uid, [('location_id', '=', location.location_id.id),('categ_id','=',line.product_id.categ_id.id)])
                    if lineqty_ids:
                        if line.product_id.use_location_qty:
                            lineqty = lineqty_obj.browse(cr, uid, lineqty_ids)[0]           
                            #POP-007                 
                            new_qty = ((lineqty.quantity * (1/(line.omg_ratio or 1.0))) / (line.omg_sampling or 1.0)) * int(total_day)
                            #POP-009
                            new_qty = round(new_qty)
                    else:
                        if line.product_id.customer_material:
                            raise osv.except_osv(_('No Product Estimate'), _('Please define product ('+ line.product_id.name +') estimate in location \n'+location.location_id.name+' | '+line.product_id.categ_id.name+'.'))                                        
                        else:
                            #POP-007
                            new_qty = ((line.product_uom_qty * (1/(line.omg_ratio or 1.0))) / (line.omg_sampling or 1.0)) * int(total_day)
                            #POP-009
                            new_qty = round(new_qty)
                #POP-023
                #DAY-001 ต่ำกว่า 0.25 = 0 , 0.25-0.75 = 0.5 , 0.76+ = 1
                if line.product_id.uom_id <> line.product_id.warehouse_uom and line.product_id.full_warehouse_uom:
                    full_warehouse_qty = round(1/(line.product_id.warehouse_uom.factor or 1))
                    if full_warehouse_qty > 1:
                        lesspack = round(new_qty,2) % round(full_warehouse_qty,2)
                        fullpack = round(new_qty,2) / round(full_warehouse_qty,2)
                        if fullpack:
                            if fullpack > 1:
                                #fullpack = round(fullpack)
                                fullpack = round(new_qty,2) // round(full_warehouse_qty,2)
                                less_ratio = lesspack / full_warehouse_qty
                                if less_ratio and less_ratio >= 0.75:
                                    fullpack = fullpack + 1
                                    new_qty = fullpack * full_warehouse_qty
                                elif less_ratio and less_ratio >= 0.25:
                                    fullpack = fullpack + 0.5
                                    new_qty = round(fullpack * full_warehouse_qty)
                                else:
                                    new_qty = fullpack * full_warehouse_qty
                            else:
                                new_qty = new_qty
                        else:
                            new_qty = new_qty

            for location in line.order_id.sale_location_ids:
                new_data = {               
                    'name': line.name,
                    'order_id': line.order_id.id,
                    'sale_line_id': line.id,
                    'location_id': location.location_id.id,
                    'delivery_type_id': False,
                    'process': True,
                    'product_id': line.product_id.id,
                    'pm_qty': new_qty, # line.product_uom_qty,
                    'pm_uom_id': line.product_uom.id,
                    'note': False,
                }
                line_branch_id = self.pool.get('sale.order.line.branch').create(cr ,uid, new_data)                
            
        return True
    
#    def write(self, cr, uid, ids, vals, context=None):
#        cur_obj = self.pool.get('res.currency')
#        res = {}
#        if context is None:
#            context = {}
#        sum_price = 0.0            
#        for line in self.browse(cr, uid, ids, context=context):
#            price_unit = self.pool.get('product.pricelist').price_get(cr, uid, [line.order_id.pricelist_id.id], line.product_id.id, 1.0, line.order_id.partner_id.id, {'date': line.order_id.date_order, 'uom': line.product_id.uom_id.id })[line.order_id.pricelist_id.id]            
#            cur = line.order_id.pricelist_id.currency_id            
#            res[line.id] = cur_obj.round(cr, uid, cur, price_unit)

#            total_day = 1
#            if line.with_period and line.order_id.sale_period_days:
#                total_day = line.order_id.sale_period_days
#            total_location = 1
#            if line.with_branch and line.order_id.sale_location_counts:
#                total_location = line.order_id.sale_location_counts
#            sum_price = int(total_day) * price_unit * int(total_location)

#            if vals.get('price_unit', False) and sum_price != 0:
#                vals.update({'price_unit': sum_price})                                    
#        return super(sale_order_line, self).write(cr, uid, ids, vals, context=context)    

    def invoice_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        def _get_line_qty(line):
            if (line.order_id.invoice_quantity=='order') or not line.procurement_id:
                if line.product_uos:
                    return line.product_uos_qty or 0.0
                return line.product_uom_qty
            else:
                return self.pool.get('procurement.order').quantity_get(cr, uid,
                        line.procurement_id.id, context=context)

        def _get_line_uom(line):
            if (line.order_id.invoice_quantity=='order') or not line.procurement_id:
                if line.product_uos:
                    return line.product_uos.id
                return line.product_uom.id
            else:
                return self.pool.get('procurement.order').uom_get(cr, uid,
                        line.procurement_id.id, context=context)

        create_ids = []
        sales = {}
        for line in self.browse(cr, uid, ids, context=context):
            if not line.invoiced:
                if line.product_id:
                    a = line.product_id.product_tmpl_id.property_account_income.id
                    if not a:
                        a = line.product_id.categ_id.property_account_income_categ.id
                    if not a:
                        raise osv.except_osv(_('Error !'),
                                _('There is no income account defined ' \
                                        'for this product: "%s" (id:%d)') % \
                                        (line.product_id.name, line.product_id.id,))
                else:
                    prop = self.pool.get('ir.property').get(cr, uid,
                            'property_account_income_categ', 'product.category',
                            context=context)
                    a = prop and prop.id or False
                uosqty = _get_line_qty(line)
                uos_id = _get_line_uom(line)
                pu = 0.0
                if not line.with_period and not line.with_branch:
                    new_qty = uosqty
                else:
                    total_day = 1
                    if line.with_period and line.order_id.sale_period_days:
                        #total_day = line.order_id.sale_period_days or 1.0
                        #POP-012
                        total_day = line.order_id.price_period_days or 1.0  
                    total_location = 1
                    if line.with_branch and line.order_id.sale_location_counts:
                        total_location = line.order_id.sale_location_counts or 1.0
                    new_qty = int(total_day) * int(total_location)
                if uosqty:
                    pu = round(line.price_unit * line.product_uom_qty / uosqty,
                        self.pool.get('decimal.precision').precision_get(cr, uid, 'Sale Price'))
                fpos = line.order_id.fiscal_position or False
                a = self.pool.get('account.fiscal.position').map_account(cr, uid, fpos, a)
                if not a:
                    raise osv.except_osv(_('Error !'),
                                _('There is no income category account defined in default Properties for Product Category or Fiscal Position is not defined !'))
                inv_id = self.pool.get('account.invoice.line').create(cr, uid, {
                    'name': line.name,
                    'origin': line.order_id.name,
                    'account_id': a,
                    'price_unit': pu,
                    'quantity': new_qty or uosqty,
                    'discount': line.discount,
                    'uos_id': uos_id,
                    'product_id': line.product_id.id or False,
                    'invoice_line_tax_id': [(6, 0, [x.id for x in line.tax_id])],
                    'note': line.notes,
                    'account_analytic_id': line.order_id.project_id and line.order_id.project_id.id or False,
                })
                cr.execute('insert into sale_order_line_invoice_rel (order_line_id,invoice_id) values (%s,%s)', (line.id, inv_id))
                self.write(cr, uid, [line.id], {'invoiced': True})
                sales[line.order_id.id] = True
                create_ids.append(inv_id)
        # Trigger workflow events
        wf_service = netsvc.LocalService("workflow")
        for sid in sales.keys():
            wf_service.trg_write(uid, 'sale.order', sid, cr)
        return create_ids


    def my_product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, 
            fiscal_position=False, flag=False, price_unit=False):
        if not  partner_id:
            raise osv.except_osv(_('No Customer Defined !'), _('You have to select a customer in the sales form !\nPlease set one customer before choosing a product.'))
        warning = {}
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        if partner_id:
            lang = partner_obj.browse(cr, uid, partner_id).lang
        context = {'lang': lang, 'partner_id': partner_id}

        if not product:
            return {'value': {'th_weight': 0, 'product_packaging': False,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                   'product_uos': []}}
        if not date_order:
            date_order = time.strftime('%Y-%m-%d')

        result = {}
        product_obj = product_obj.browse(cr, uid, product, context=context)
        if not packaging and product_obj.packaging:
            packaging = product_obj.packaging[0].id
            result['product_packaging'] = packaging

        if packaging:
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            pack = self.pool.get('product.packaging').browse(cr, uid, packaging, context=context)
            q = product_uom_obj._compute_qty(cr, uid, uom, pack.qty, default_uom)
#            qty = qty - qty % q + q
            if qty and (q and not (qty % q) == 0):
                ean = pack.ean or _('(n/a)')
                qty_pack = pack.qty
                type_ul = pack.ul
                warn_msg = _("You selected a quantity of %d Units.\n"
                            "But it's not compatible with the selected packaging.\n"
                            "Here is a proposition of quantities according to the packaging:\n\n"
                            "EAN: %s Quantity: %s Type of ul: %s") % \
                                (qty, ean, qty_pack, type_ul.name)
                warning = {
                    'title': _('Picking Information !'),
                    'message': warn_msg
                    }
            result['product_uom_qty'] = qty

        uom2 = False
        
        result['uom_category_id'] = product_obj.uom_id.category_id.id,
        #POP-004
        result['apply_all_store'] = not product_obj.use_location_qty
        
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False
        if product_obj.description_sale:
            result['notes'] = product_obj.description_sale
        fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        if update_tax: #The quantity only have changed
            result['delay'] = (product_obj.sale_delay or 0.0)
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product_obj.taxes_id)
            result.update({'type': product_obj.procure_method})

        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context)[0][1]
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}

        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight        # Round the quantity up

        if not uom2:
            uom2 = product_obj.uom_id
        if (product_obj.type=='product') and (product_obj.virtual_available * uom2.factor < qty * product_obj.uom_id.factor) \
          and (product_obj.procure_method=='make_to_stock'):
            warning = {
                'title': _('Not enough stock !'),
                'message': _('You plan to sell %.2f %s but you only have %.2f %s available !\nThe real stock is %.2f %s. (without reservations)') %
                    (qty, uom2 and uom2.name or product_obj.uom_id.name,
                     max(0,product_obj.virtual_available), product_obj.uom_id.name,
                     max(0,product_obj.qty_available), product_obj.uom_id.name)
            }
        # get unit price
        if not pricelist:
            warning = {
                'title': 'No Pricelist !',
                'message':
                    'You have to select a pricelist or a customer in the sales form !\n'
                    'Please set one before choosing a product.'
                }
        else:
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                    product, qty or 1.0, partner_id, {
                        'uom': uom,
                        'date': date_order,
                        })[pricelist]
            if price is False:
                warning = {
                    'title': 'No valid pricelist line found !',
                    'message':
                        "Couldn't find a pricelist line matching this product and quantity.\n"
                        "You have to change either the product, the quantity or the pricelist."
                    }
            else:
                if not price_unit:
                    result.update({'price_unit': price})
                else:
                    if price_unit == 1:
                        result.update({'price_unit': price})
                        
        return {'value': result, 'domain': domain, 'warning': warning}

    def my_product_uom_change(self, cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, price_unit=False):
        res = self.my_product_id_change(cursor, user, ids, pricelist, product,
                qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name,
                partner_id=partner_id, lang=lang, update_tax=update_tax,
                date_order=date_order,price_unit=price_unit)
        if 'product_uom' in res['value']:
            del res['value']['product_uom']
        if not uom:
            res['value']['price_unit'] = 1.0
        return res
    
sale_order_line()

class omg_sale_chain(osv.osv):
    _name = "omg.sale.chain"
    _description = "Chain"
    _columns = {
        'name': fields.char('Chain', size=100, required=True),
        'image_url': fields.char('Image URL', size=240),
    }
    _sql_constraints = [
        ('sale_chain_unique','unique (name)', 'Chain must me unique.')
    ]
omg_sale_chain()

class omg_sale_location_group(osv.osv):
    _name = "omg.sale.location.group"
    _description = "Location Group"
    _columns = {
        'name': fields.char('Location Group',size=32,required=True),
    }
    _sql_constraints = [
        ('sale_location_group_unique','unique (name)', 'Location group must me unique.')
    ]
omg_sale_location_group()

class omg_sale_location_type(osv.osv):
    _name = "omg.sale.location.type"
    _description = "Location Type"
    _columns = {
        'name': fields.char('Location Type',size=32,required=True),
        'product_id':fields.many2one('product.product', 'Service Cost', required=False),
    }
    _sql_constraints = [
        ('sale_location_type_unique','unique (name)', 'Location type must me unique.')
    ]
omg_sale_location_type()

class stock_location(osv.osv):
    _name = "stock.location"
    _inherit = "stock.location"
    _description = "Sale extended of Location"
    _columns = {
        'chain_id': fields.many2one('omg.sale.chain', 'Chain', ondelete="restrict"),
        'location_group_id': fields.many2one('omg.sale.location.group', 'Group', ondelete="restrict"),
        'location_type_id': fields.many2one('omg.sale.location.type', 'Type', ondelete="restrict"),
        #'location_group_spedical_ids': fields.one2many('omg.stock.location.group.special','location_id','Group Special'),
        'location_group_spedical_ids': fields.many2many('omg.sale.group.special', 'sale_group_special_rel',
            'location_id', 'group_id', 'Group Special'),
        
    }
stock_location()

class omg_sale_location_group_special_query(osv.osv):
    _name = 'omg.sale.location.group.special.query'
    _description = 'Special group of location.'
    _auto = False
    _columns = {
        'location_id': fields.many2one('stock.location', 'Location'),
        'group_id': fields.many2one('omg.sale.group.special', 'Special Group'),
    }
    _order = "location_id"
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'omg_sale_location_group_special_query')
        cr.execute("""
            create or replace view omg_sale_location_group_special_query as 
                select id, (a[id]).* from (select a, generate_series(1, array_upper(a,1)) as id from (
                select array (select sale_group_special_rel from sale_group_special_rel) as a ) b ) c 
        """)
    
omg_sale_location_group_special_query()

#DAY-006
class omg_sale_location_booth_type(osv.osv):
    _name = "omg.sale.location.booth.type"
    _description = "Specific Booth Type"
    _columns = {
        'name': fields.char('Specific Booth Type',size=32,required=True),
    }
    _sql_constraints = [
        ('sale_location_booth_type_unique','unique (name)', 'Specific Booth Type must me unique.')
    ]
omg_sale_location_booth_type()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
