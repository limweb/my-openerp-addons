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

# 27-02-2012    POP-001    Add Max Category in stock.location.booking
# 5-03-2012     POP-002    Add Estimate
# 12-03-2012    POP-003    Item Sale Check
# 12-03-2012    POP-004    Not Send Data to Sale Order
# 12-03-2012    POP-005    Add Sale Admin
# 01-04-2012    POP-006    Add Default Product -> Period = True
# 17-04-2012    POP-007    Add Check Max Count In Contact Reservation
# 18-04-2012    POP-008    Add Period & Chain in Contact Reservatino
# 18-04-2012    POP-009    Add FOS No 
# 28-05-2012    DAY-001    Del Location, Copy Contact add booking History
# 30-05-2012    DAY-002    Set State Draft 
# 30-05-2012    DAY-003    Update Sale Branch line
# 11-06-2012    DAY-004    Check Categ,Check Place
# 11-07-2012    DAY-005    Check Categ
# 23-07-2012    DAY-006    Update Copy Contact
# 23-07-2012    DAY-007    Cash Advance Other
# 30-07-2012    DAY-008    Add Type Location contact_line_location
# 14-08-2012    DAY-009    Add specific_booth_type
# 25-08-2012    DAY-010    Materials Cash Adv
# 24-09-2012    DAY-011    Fos , Estimate, client_price 

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import time
import netsvc
import decimal_precision as dp
from operator import itemgetter

from osv import fields,osv
from tools.translate import _

class omg_sale_reserve_contact(osv.osv):

    def _count_location(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = 0
        return res

    def _count_period(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = 0
        return res

    def _get_period_first(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            period_str = ""
            for detail in line.line_ids:
                period_str = detail.period_id.name
            res[line.id] = period_str
        return res

    def _get_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            grand_total = 0
            for detail in line.line_ids:
                grand_total = grand_total + detail.sub_total
            res[line.id] = grand_total or 0.0
        return res

    _name = "omg.sale.reserve.contact"
    _description = "Extend for OMG Holding (Thailand) Co.,Ltd."

    _columns = {
        'name': fields.char('Booking No', size=32, required=True),
        #DAY-011
        #'contact_date': fields.datetime("Contact Date", required=True),
        'contact_date': fields.date("Contact Date", required=True),
        'customer_id': fields.many2one('res.partner', 'Customer', required=True, ondelete="restrict"),
        'product_id': fields.many2one('product.product', 'Customer Product', required=True, ondelete="restrict"),
        'service_id': fields.many2one('product.product', 'Service Type', required=True, ondelete="restrict"),
        'saleman_id': fields.many2one('res.users', 'Salesman' ,required=True, ondelete="restrict"),
        'note': fields.text('Notes'),
        'location_qty': fields.function(_count_location, method=True, type='integer', string='Location Qty'),
        'period_qty': fields.function(_count_period, method=True, type='integer', string='Period Qty'),
        'total': fields.function(_get_total, method=True, type='float', string='Total'),
        'line_ids': fields.one2many('omg.sale.reserve.contact.line', 'contact_id', 'Line of Contact'),
        'total_amount': fields.float('Amount'),
        'company_id': fields.many2one('res.company', 'Company', required=True), 
        'period_first': fields.function(_get_period_first, method=True, type='string', string='Period Name'),
        #POP-005
        'sale_admin_id': fields.many2one('res.users', 'Sale Admin' ,required=True, ondelete="restrict"),
        #POP-008
        'chain_id': fields.many2one('omg.sale.chain','Chain'),
        'period_id': fields.many2one('omg.sale.period','Period'),
        #POP-009
        'fos_contact_no': fields.char('FOS No', size=50,),
        #DAY-011
        'credit_term': fields.char('Credit Term', size=250,),        
        
    }    

    _defaults = {
        'name': '/', #lambda self,cr,uid,ctx={}: self.pool.get('ir.sequence').get(cr, uid, 'omg.contact.type') or '/',
        'saleman_id': lambda self, cr, uid, context: uid,
        #POP-005
        'sale_admin_id': lambda self, cr, uid, context: uid,
        #DAY-011
        #'contact_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'contact_date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }
    
    _sql_constraints = [
        ('sale_reserve_uniq', 'unique (name)', 'Contact No must be unique.')
    ]    
    
    def create(self, cr, user, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            sequence_id = self.pool.get('ir.sequence').get(cr, user, 'omg.contact.type')
            if not sequence_id:                
                raise osv.except_osv(_('Error !'), _('Can not find Reservation Contact Sequence for Company.'))                
            vals['name'] = sequence_id
            
        return super(omg_sale_reserve_contact,self).create(cr, user, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            period_id = False
            chain_id = False
            for line in line.line_ids:
                if not period_id:
                    period_id = line.period_id.id or False
                if not chain_id:
                    chain_id = line.chain_id.id or False
                location_book_ids = self.pool.get('stock.location.booking').search(cr, uid, [('contact_line_id','=',line.id)])
                if location_book_ids:
                    for booking in self.pool.get('stock.location.booking').browse(cr, uid, location_book_ids):
                        booking.write({'period_id':line.period_id.id})
            vals.update({'period_id': period_id,'chain_id': chain_id})
                                    
        return super(omg_sale_reserve_contact, self).write(cr, uid, ids, vals, context=context)

    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        data = self.browse(cr, uid, id, context=context)
        new_child_ids = []
        if not default:
            default = {}
        default = default.copy()
        default['name'] = self.pool.get('ir.sequence').get(cr, uid, 'omg.contact.type') #(data['name'] or '') + ' (copy)'
        res = super(omg_sale_reserve_contact, self).copy(cr, uid, id, default, context=context)
        if res:
            reserve_obj = self.browse(cr, uid, res, context=context)
            for move in reserve_obj.line_ids:
                move.write({'sale_order_id': False})
                for line in move.location_lines:
                    location_booking = {'contact_line_id':move.id,'contact_id':reserve_obj.id ,
                                        'product_id': reserve_obj.product_id.id, 'category_id': reserve_obj.product_id.categ_id.id,
                                        'period_id': move.period_id.id,'location_id': line.location_id.id ,
                                        'group_id':line.location_id.location_group_id.id ,
                                        'chain_id': move.chain_id.id,'saleman_id':reserve_obj.saleman_id.id,
                                        'service_category_id':reserve_obj.service_id.categ_id.id,
                                        'ineco_check_place':reserve_obj.service_id.categ_id.ineco_check_place,
                                       #DAY-006 
                                        'ineco_check_cate':reserve_obj.service_id.categ_id.ineco_check_categ}                        
                    self.pool.get('stock.location.booking').create(cr, uid, location_booking)                
        return res


omg_sale_reserve_contact()

class omg_sale_reserve_contact_line(osv.osv):
    
    def _get_location_list(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            location_list = ""
            for location in line.location_lines:
                if location.location_id.location_group_id:
                    location_list = location_list+location.location_id.name+' ('+location.location_id.location_group_id.name+"), "
                else:
                    location_list = location_list+location.location_id.name+", "
            res[line.id] = location_list
        return res

    def _count_location(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            location_qty = 0
            for location in line.location_lines:
                location_qty = location_qty + 1
            res[line.id] = location_qty
        return res

    def _get_unitprice(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            other_price = 0
            for product in line.product_lines:
                other_price += product.sub_total
            res[line.id] =  other_price
        return res     
    
    def _get_summary_total(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            other_price = 0
            for summary in line.summary_lines:
                other_price += summary.sub_total
            res[line.id] =  other_price
        return res   
     
    def _get_subtotal(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            product_price = 0
            summary_price = 0
            for summary in line.summary_lines:
                summary_price += summary.sub_total
            for product in line.product_lines:
                product_price += product.sub_total              
            res[line.id] =  summary_price + product_price
        return res
    
    def _get_default_price(self, cr, uid, context=None):
        if not context:
            context = {}
        unit_price = 0
        if context.get('active_id'):
            contact = self.pool.get('omg.sale.reserve.contact').browse(cr, uid, context['active_id'], context=context)
            if contact:
                #DAY-011
                #unit_price = contact.service_id.list_price
                unit_price = 0
        return unit_price
    
    _name = "omg.sale.reserve.contact.line"
    _description = "Line of Contacts"
    _columns = {
        'name': fields.char('Description', size=100),
        'contact_id': fields.many2one('omg.sale.reserve.contact', 'Contact',required=True, ondelete="restrict"),
        'period_id': fields.many2one('omg.sale.period','Period',required=True,readonly=True, states={'reserve':[('readonly', False)],'inprogress': [('readonly', False)]}, ondelete="restrict"),
        'chain_id': fields.many2one('omg.sale.chain', 'Chain',required=True,readonly=True, states={'reserve':[('readonly', False)],'inprogress': [('readonly', False)]}, ondelete="restrict"),
        'category_id': fields.many2one('product.category','Category', ondelete="restrict"),
        'location_list': fields.function(_get_location_list, method=True, type='char', string="Location Detail",readonly=True,),
        'location_qty': fields.function(_count_location, method=True, type='integer', string="Location QTY"),
        'sale_order_id': fields.many2one('sale.order','Sale Order', ondelete="restrict"),        
        'client_price': fields.float('Client Price', digits_compute= dp.get_precision('Sale Price')),        
        'summary_total': fields.function(_get_summary_total, method=True, type='float', string="Summary Total"),
        'unit_price': fields.function(_get_unitprice, method=True, type='float', string="Product Total"),
        'sub_total': fields.function(_get_subtotal, method=True, type='float', string="Total"),
        'location_lines': fields.one2many('omg.sale.reserve.contact.line.location','contact_line_id','Locations',readonly=True, states={'reserve':[('readonly', False)],'inprogress': [('readonly', False)]}),
        'product_lines': fields.one2many('omg.sale.reserve.contact.line.product','contact_line_id','Products',readonly=True, states={'reserve':[('readonly', False)],'inprogress': [('readonly', False)]}),
        'summary_lines': fields.one2many('omg.sale.reserve.contact.line.summary','contact_line_id','Summary',readonly=True, states={'reserve':[('readonly', False)],'inprogress': [('readonly', False)]}),
        'state': fields.selection([('reserve', 'Reserved'), ('inprogress', 'In-Progress'), ('done', 'Done'),('cancel','Cancel')], 'State', readonly=True, select=True),
        'allow_duplicate': fields.boolean('Allow Duplicate Category'),
        #POP-003
        #'item_sale_check_ids': fields.many2many('product.product', 'product_product_contact_check_rel', 'contact_id', 'product_tmpl_id', 'Item Check Sales'),                
        #DAY-011
        'category_es_id': fields.many2one('product.category','Category Estimate',readonly=True, states={'reserve':[('readonly', False)],'inprogress': [('readonly', False)]}, ondelete="restrict"),
        
    }
    _defaults = {
        'state': 'reserve',
        'allow_duplicate': False,
        'client_price': 0 ,
    }

    _sql_constraints = [
        ('sale_reserve_line_uniq', 'unique (contact_id,period_id,chain_id)', 'Period and Chain must be unique.')
    ]

#    def write(self, cr, uid, ids, vals, context=None):
#        if context is None:
#            context = {}
#        contact_obj = self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, ids[0])
#        location_book_ids = self.pool.get('stock.location.booking').search(cr, uid, [('contact_line_id','=',ids[0])])
#        if location_book_ids:
#            for booking in self.pool.get('stock.location.booking').browse(cr, uid, location_book_ids):
#                booking.write({'period_id':contact_obj.period_id.id})
                                                   
#        return super(omg_sale_reserve_contact_line, self).write(cr, uid, ids, vals, context=context)
        
    def action_process(self, cr, uid, ids, context=None):
        location_book_ids = self.pool.get('stock.location.booking').search(cr, uid, [('contact_line_id','=',ids[0])])
        if location_book_ids:
            for booking in self.pool.get('stock.location.booking').browse(cr, uid, location_book_ids):
                booking.write({'state':'booking'})
        self.write(cr, uid, ids, {'state':'inprogress'})
        return []
    
    def action_draft(self, cr, uid, ids, context=None):
        contact_obj = self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, ids)[0]
        if contact_obj.sale_order_id:
            if contact_obj.sale_order_id.state == 'draft':        
                location_book_ids = self.pool.get('stock.location.booking').search(cr, uid, [('contact_line_id','=',ids[0])])
                if location_book_ids:
                    for booking in self.pool.get('stock.location.booking').browse(cr, uid, location_book_ids):
                        booking.write({'state':'draft'})
                self.write(cr, uid, ids, {'state':'reserve'})
            else:
                raise osv.except_osv(_('Warning'), _("ข้อมูล SaleOrder state ไม่เป็น draft กรุณา set draft ด้วยครับ"))   #DAY-010          
        return []

    def _check_booking(self, cr, uid, ids, context=None):
        can_book = True
        contact_obj = self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, ids)[0]
        self.allow = contact_obj.allow_duplicate
        if contact_obj.contact_id.service_id.categ_id.ineco_check_categ:
            for location in contact_obj.location_lines:
                if can_book:
                    can_book = self._can_booking(cr, uid, ids, location.location_id.id, contact_obj.category_id.id, contact_obj.period_id.id, contact_obj.contact_id.service_id.categ_id.id )
        return can_book
    
    def _get_max_service(self, cr, uid, ids, location_id, service_categ_id, context=None):
        result = 1000
        service_ids = self.pool.get('ineco.stock.location.category.max').search(cr, uid, [('location_id','=',location_id),('category_id','=',service_categ_id)])
        if service_ids:
            service = self.pool.get('ineco.stock.location.category.max').browse(cr, uid, service_ids)[0]
            if service.category_id.ineco_check_place:
                result = service.quantity
        return result
    
    def _get_period_ids(self, cr, uid, ids, period_id, context=None):
        if not period_id:
            raise osv.except_osv(_('Warning'), _('Period is empty.')) 
        
        period = self.pool.get('omg.sale.period').browse(cr, uid, [period_id])[0]
        
        sql = """
               select osp.id from omg_sale_period osp
               where 
                 (osp.date_start between '%s' and '%s') and
                 (osp.date_finish <= '%s')
        """
        cr.execute(sql % (period.date_start, period.date_finish, period.date_finish))
        ids = map(itemgetter(0), cr.fetchall())
        return ids
    
    def _can_booking(self, cr, uid, ids, location_id, category_id, period_id, service_categ_id, context=None):
        period_ids = self._get_period_ids(cr, uid, ids, period_id)
        if not period_ids:
            raise osv.except_osv(_('Warning'), _('List of Period is empty.'))       
        #DAY-005
        booking_ids = self.pool.get('stock.location.booking').search(cr, uid,[('location_id','=',location_id),('period_id','in',period_ids),('category_id','=',category_id),('state','!=','cancel'),('ineco_check_cate','=',1),('contact_line_id','!=',ids[0])])
        max_ids = self.pool.get('stock.location.booking').search(cr, uid,[('location_id','=',location_id),('period_id','in',period_ids),('state','!=','cancel'),('service_category_id','=',service_categ_id),('ineco_check_place','=',1),('contact_line_id','!=',ids[0])])
        can_book = True
        location = self.pool.get('stock.location').browse(cr, uid, [location_id])[0]
        contact_obj = self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, ids)[0]
        #DAY 004
        if contact_obj.contact_id.service_id.categ_id.ineco_check_categ:        
            if contact_obj.allow_duplicate:
                booking_ids = []
            else:
                if len(booking_ids) > 0:
                    raise osv.except_osv(_('Warning'), _('You have selected Duplication Category')) 
        #DAY 004
        if contact_obj.contact_id.service_id.categ_id.ineco_check_place: 
            #POP-007
            if location and location.max_place_qty == 0:
                can_book = True
            elif location and location.max_place_qty < len(max_ids):
                can_book = False
                raise osv.except_osv(_('Warning'), _('You have Over Max Place can be sold ->'+location.name+', ' + str(location.max_place_qty)+','+str(len(max_ids)) ))            
                      
            #POP-001
            max_service_qty = self._get_max_service(cr,uid,ids,location.id, service_categ_id, context)
            if len(booking_ids) == 0 and location and max_service_qty > len(max_ids):
                can_book = True
            else:
                can_book = False
                raise osv.except_osv(_('Warning'), _('You have Over Max Service can be sold ->'+location.name+', ' + contact_obj.contact_id.service_id.categ_id.name))            
        return can_book
    
    def _make_cancel(self, cr, uid, ids, location_id, category_id, period_id, context=None):
        booking_ids = self.pool.get('stock.location.booking').search(cr, uid,[('location_id','=',location_id),('period_id','=',period_id),('category_id','=',category_id),('state','!=','done')])
    
        if booking_ids:
            for line in self.pool.get('stock.location.booking').browse(cr, uid, booking_ids):
#                line.write({'state':'cancel'})
                self._send_request(cr, uid, ids, context, line.contact_id.name, line.location_id.name, line.saleman_id)
        return True
    
    def _send_request(self, cr, uid, ids, context, bookingno, location_name, to_sale):
        request = self.pool.get('res.request')
        summary = '''Your reservation contact document has been change by another approve reservation.

        Booking No: %s
        Location Changed: %s
        By: %s
        \n'''% (bookingno, location_name, to_sale.name)
        request.create(cr, uid,
            {'name': "Booking Exception.",
                'act_from': uid,
                'act_to': to_sale.id,
                'body': summary,
            })
        return True

    def action_done(self, cr, uid, ids, context=None):
        user_id = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        contact_obj = self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, ids)[0]
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id','=',user_id.company_id.id)])
        shop_id = self.pool.get('sale.shop').browse(cr, uid, shop_ids)[0]
        if self._check_booking(cr, uid, ids, context):
            sale_order_obj = self.pool.get('sale.order')
            if contact_obj.sale_order_id:
                if contact_obj.sale_order_id.state == 'draft':
                    location_book_ids = self.pool.get('stock.location.booking').search(cr, uid, [('contact_line_id','=',ids[0])])
                    sale_branch_line_locations = self.pool.get('sale.branch.line').search(cr, uid, [('sale_id','=',contact_obj.sale_order_id.id)]) 
                    bookings = []
                    sale_branch_lines = []
                    if location_book_ids:
                        for booking in self.pool.get('stock.location.booking').browse(cr, uid, location_book_ids):    
                            bookings.append(booking.location_id.id)                           
                    if sale_branch_line_locations:
                        for sale_branch_line in self.pool.get('sale.branch.line').browse(cr, uid, sale_branch_line_locations):
                            sale_branch_lines.append(sale_branch_line.location_id.id)
                    sale_branch_location_del = list(set(sale_branch_lines) - set(bookings))
                    sale_branch_location_add = list(set(bookings) - set(sale_branch_lines))
                    
                    if sale_branch_location_del:
                        if len(sale_branch_location_del) == 1:
                            for locaton_del in sale_branch_location_del:
                                sql_delete_branch = 'delete from sale_branch_line where sale_id =%s and location_id = %s' % (contact_obj.sale_order_id.id,locaton_del)
                                cr.execute(sql_delete_branch)                        
                                cr.commit()
                                #DAY-007
                                sql_delete_cash_advance ='delete from sale_cash_advance_other_line where sale_id=%s and location_id = %s' % (contact_obj.sale_order_id.id,locaton_del)                                
                                cr.execute(sql_delete_cash_advance)                        
                                cr.commit()
                                #DAY-010
                                sql_delete_cash_advance_mat ='delete from sale_cash_advance_material_line where sale_id=%s and location_id = %s' % (contact_obj.sale_order_id.id,locaton_del)                                
                                cr.execute(sql_delete_cash_advance_mat)                        
                                cr.commit()
                        else:
                            sql_delete_branch = 'delete from sale_branch_line where sale_id =%s and location_id in %s' % (contact_obj.sale_order_id.id,tuple(sale_branch_location_del))
                            cr.execute(sql_delete_branch)                        
                            cr.commit()
                            #DAY-007
                            sql_delete_cash_advance = 'delete from sale_cash_advance_other_line where sale_id=%s and location_id in %s' % (contact_obj.sale_order_id.id,tuple(sale_branch_location_del))
                            cr.execute(sql_delete_cash_advance)                        
                            cr.commit()
                            #DAY-010
                            sql_delete_cash_advance_mat ='delete from sale_cash_advance_material_line where sale_id=%s and location_id in %s' % (contact_obj.sale_order_id.id,tuple(sale_branch_location_del))                              
                            cr.execute(sql_delete_cash_advance_mat)                        
                            cr.commit()                            
                            
                    if sale_branch_location_add:
                        sale_branch_obj = self.pool.get('sale.branch.line')
                        #DAY-007
                        sale_cash_advance_obj = self.pool.get('sale.cash.advance.other.line')
                        #DAY-010
                        sale_cash_advance_mat = self.pool.get('sale.cash.advance.material.line')
                        for lid in sale_branch_location_add:
                            location = self.pool.get('stock.location').browse(cr,uid,[lid])[0]
                            #DAY-011
                            location_est_ids = self.pool.get('omg.sale.reserve.contact.line.location').search(cr, uid, [('contact_line_id','=',contact_obj.id),('location_id','=',location.id)])
                            if location_est_ids:
                                location_est = self.pool.get('omg.sale.reserve.contact.line.location').browse(cr, uid, location_est_ids)[0]
                            else:
                                raise osv.except_osv(_('Warning'), _("ข้อมูลมีปัญหากรุณาติดต่อผู้ดูแลระบบ"))
                            #location_categ_ids = self.pool.get('stock.location.line.qty').search(cr, uid, [('categ_id','=',contact_obj.contact_id.product_id.categ_id.id),('location_id','=',location.id)])
                            #POP-002
                            #estimate = 0
                            # if location_categ_ids:
                            #    estimate = self.pool.get('stock.location.line.qty').browse(cr, uid, location_categ_ids)[0].quantity
                            sale_branch_obj.create(cr,uid,{
                                'sale_id': contact_obj.sale_order_id.id,
                                'location_id': location.id,
                                'location_name': location.name,
                                'group': location.location_group_id.name or False,
                                'department': location.chain_id.name or False,
                                'area': location.location_type_id.name or False,
                                # DAY-011
                                # 'estimate': estimate,
                                'estimate': location_est.estimate,                              
                                })
                            #DAY-010
                            sale_cash_advance_mat.create(cr,uid,{
                                'sale_id': contact_obj.sale_order_id.id,
                                'location_id': location.id,
                                'amount': 0.0,
                                })                            
                            #DAY-007
                            location_cash_advance_ids = self.pool.get('stock.location.cash.advance.other').search(cr, uid, [('location_id','=',location.id)])                            
                            if location_cash_advance_ids:
                                for locaids in location_cash_advance_ids:
                                    cash_advance_location_obj = self.pool.get('stock.location.cash.advance.other').browse(cr, uid, [locaids])[0]
                                    sale_cash_advance_obj.create(cr,uid,{
                                            'sale_id':contact_obj.sale_order_id.id,
                                            'location_id':location.id,
                                            'amount':cash_advance_location_obj.amount,
                                            'product_id':cash_advance_location_obj.product_id.id,
                                            'cash_advance_other_id':cash_advance_location_obj.id,
                                        })
                                
                    if location_book_ids:
                        for booking in self.pool.get('stock.location.booking').browse(cr, uid, location_book_ids):
                            booking.write({'state':'done'})
                    self.write(cr, uid, ids, {'state':'done'})
                                            
                else:
                    raise osv.except_osv(_('Warning'), _("ข้อมูล SaleOrder state ไม่เป็น draft กรุณา set draft ด้วยครับ"))             
            else:               
                sale_order_id = sale_order_obj.create(cr, uid, {
                    'pricelist_id': contact_obj.contact_id.customer_id.property_product_pricelist.id,
                    'date_order': time.strftime('%Y-%m-%d'),
                    'client_order_ref': contact_obj.contact_id.name,
                    'customer_product_id': contact_obj.contact_id.product_id.id,
                    'user_id': contact_obj.contact_id.saleman_id.id or False,
                    'partner_id': contact_obj.contact_id.customer_id.id,        
                    'partner_order_id': contact_obj.contact_id.customer_id.address[0].id,    
                    'partner_invoice_id': contact_obj.contact_id.customer_id.address[0].id,    
                    'partner_shipping_id': contact_obj.contact_id.customer_id.address[0].id,    
                    'shop_id': shop_id.id,
                    'company_id': contact_obj.contact_id.company_id.id,
                    #POP-003 Check Item Sale
                    'item_sale_check_ids': [(6, 0, [x.id for x in contact_obj.contact_id.product_id.item_sale_check_ids])],
                    'service_product_id': contact_obj.contact_id.service_id.id,
                    #DAY-011
                    'note': contact_obj.contact_id.credit_term,
                })
                sale_branch_obj = self.pool.get('sale.branch.line')
                #DAY-007
                sale_cash_advance_obj = self.pool.get('sale.cash.advance.other.line')
                #DAY-010
                sale_cash_advance_mat = self.pool.get('sale.cash.advance.material.line')
                                
                for location in contact_obj.location_lines:
                    if self._can_booking(cr, uid, ids, location.location_id.id, contact_obj.category_id.id, contact_obj.period_id.id, contact_obj.contact_id.service_id.categ_id.id ):
                        #DAY-011
                        location_est_ids = self.pool.get('omg.sale.reserve.contact.line.location').search(cr, uid, [('contact_line_id','=',contact_obj.id),('location_id','=',location.location_id.id)])
                        location_est = self.pool.get('omg.sale.reserve.contact.line.location').browse(cr, uid, location_est_ids)[0]                        
                        #location_categ_ids = self.pool.get('stock.location.line.qty').search(cr, uid, [('categ_id','=',contact_obj.contact_id.product_id.categ_id.id),('location_id','=',location.location_id.id)])
                        #POP-002
                        #estimate = 0
                        #if location_categ_ids:
                        #    estimate = self.pool.get('stock.location.line.qty').browse(cr, uid, location_categ_ids)[0].quantity
                        sale_branch_obj.create(cr,uid,{
                            'sale_id': sale_order_id,
                            'location_id': location.location_id.id,
                            'location_name': location.location_id.name,
                            'group': location.location_id.location_group_id.name or False,
                            'department': location.location_id.chain_id.name or False,
                            'area': location.location_id.location_type_id.name or False,
                            #DAY-011
                            #'estimate': estimate,
                            'estimate': location_est.estimate,
                        })
                        #DAY-010
                        sale_cash_advance_mat.create(cr,uid,{
                            'sale_id': sale_order_id,
                            'location_id': location.location_id.id,
                            'amount': 0.0,
                        })                         
                        #DAY-007
                        location_cash_advance_ids = self.pool.get('stock.location.cash.advance.other').search(cr, uid, [('location_id','=',location.location_id.id)])                            
                        if location_cash_advance_ids:
                            for locaids in location_cash_advance_ids:
                                cash_advance_location_obj = self.pool.get('stock.location.cash.advance.other').browse(cr, uid, [locaids])[0]
                                sale_cash_advance_obj.create(cr,uid,{
                                        'sale_id':sale_order_id,
                                        'location_id':location.location_id.id,
                                        'amount':cash_advance_location_obj.amount,
                                        'product_id':cash_advance_location_obj.product_id.id,
                                        'cash_advance_other_id':cash_advance_location_obj.id,
                                    })
                sale_period_line_obj = self.pool.get('sale.period.line')
                sale_period_line_obj.create(cr, uid, {
                    'period_id': contact_obj.period_id.id,
                    'sale_id': sale_order_id,
                    'description': contact_obj.period_id.name,
                    'date_start': contact_obj.period_id.date_start,
                    'date_finish' : contact_obj.period_id.date_finish,
                })
                fpos = False
                sale_order_line_obj = self.pool.get('sale.order.line')
                #POP-004
                #not sending to sale order line
                #sale_order_line_obj = self.pool.get('sale.order.line')
                #sale_order_line_obj.create(cr, uid, {
                #    'order_id': sale_order_id,
                #    'product_id': contact_obj.contact_id.service_id.id,
                #    'name': contact_obj.contact_id.service_id.name,
                #    'product_uom': contact_obj.contact_id.service_id.uom_id.id,
                #    'product_uom_qty': 1,
                #    'price_unit': contact_obj.client_price or contact_obj.contact_id.service_id.list_price , #contact_obj.unit_price,
                #    'tax_id': [(6, 0, [x.id for x in contact_obj.contact_id.service_id.taxes_id])],
                #})        
                #
                
                for product in contact_obj.product_lines:
                    sale_order_line_obj.create(cr, uid, {
                        'order_id': sale_order_id,
                        'product_id': product.product_id.id,
                        'name': product.product_id.name,
                        'product_uom': product.product_id.uom_id.id,
                        'product_uom_qty': product.product_qty,
                        #'with_branch': False,
                        #POP-005
                        'with_period': True,
                        'with_branch': True,
                        'apply_all_store': True,
                        'price_unit': product.sale_price ,
                        'tax_id': [(6, 0, [x.id for x in product.product_id.taxes_id])] ,
                    })
    
                for product in contact_obj.summary_lines:
                    sale_order_line_obj.create(cr, uid, {
                        'order_id': sale_order_id,
                        'product_id': product.product_id.id,
                        'name': product.product_id.name,
                        'product_uom': product.product_id.uom_id.id,
                        'product_uom_qty': product.product_qty,
                        'price_unit': product.sale_price, #product.unit_price ,
                        #DAY-011
                        'with_branch': product.with_branch,
                        'with_period': product.with_period,
                        'apply_all_store': True,
                        'tax_id': [(6, 0, [x.id for x in product.product_id.taxes_id])] ,
                    })
    
                location_book_ids = self.pool.get('stock.location.booking').search(cr, uid, [('contact_line_id','=',ids[0])])
                if location_book_ids:
                    for booking in self.pool.get('stock.location.booking').browse(cr, uid, location_book_ids):
                        booking.write({'state':'done','order_id':sale_order_id})
                    
                self.write(cr, uid, ids, {'state':'done','sale_order_id':sale_order_id})
                
                for location in contact_obj.location_lines:
                    self._make_cancel(cr, uid, ids, location.location_id.id, contact_obj.category_id.id, contact_obj.period_id.id )
    
    #        for location in contact_obj.location_lines:
    #            request = "select location_id, chain_id, period_id from omg_sale_reserve_contact_line_location a " \
    #                      "join omg_sale_reserve_contact_line b on a.contact_line_id = b.id " \
    #                      "where chain_id = %s and period_id = %s and location_id = %s and contact_line_id <> %s"
    #            cr.execute(request % (contact_obj.chain_id, contact_obj.period_id, location.id, contact_obj.id))
    #            for res in cr.dictfetchall():
    #                accounts[res['id']] = res           
        return []
    def unlink(self, cr, uid, ids, context=None, check=True):
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.state == 'done':
                raise osv.except_osv(_('Warning'), _('Not Delete State = Done'))                 
        return super(omg_sale_reserve_contact_line, self).unlink(cr, uid, ids, context)
    
    #DAY-011 
    def set_estimate(self, cr, uid, ids, context=None):
        res = {}        
        for contact_line in self.browse(cr, uid, ids, context):                 
            location_est_ids = self.pool.get('omg.sale.reserve.contact.line.location').search(cr, uid, [('contact_line_id','=',contact_line.id)])
            location_est = self.pool.get('omg.sale.reserve.contact.line.location').browse(cr, uid, location_est_ids)
            if contact_line.category_es_id:
                for location in location_est:                
                    location_categ_ids = self.pool.get('stock.location.line.qty').search(cr, uid, [('categ_id','=',contact_line.category_es_id.id),('location_id','=',location.location_id.id)])
                    estimate = 0
                    if location_categ_ids:
                        estimate = self.pool.get('stock.location.line.qty').browse(cr, uid, location_categ_ids)[0].quantity                   
                        estimate = estimate * contact_line.period_id.date_total
                    location.write({'estimate': estimate}) 
            else:
                for location in location_est:
                    location_categ_ids = self.pool.get('stock.location.line.qty').search(cr, uid, [('categ_id','=',contact_line.contact_id.product_id.categ_id.id),('location_id','=',location.location_id.id)])
                    estimate = 0
                    if location_categ_ids: 
                        estimate = self.pool.get('stock.location.line.qty').browse(cr, uid, location_categ_ids)[0].quantity                   
                        estimate = estimate * contact_line.period_id.date_total
                    location.write({'estimate': estimate})                  
        return res  

omg_sale_reserve_contact_line()

class omg_sale_reserve_contact_line_location(osv.osv):
    
    def _get_group(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.location_id and line.location_id.location_group_id :                
                res[line.id] = line.location_id.location_group_id.name
        return res


#DAY-011
    def _get_format(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.location_id and line.location_id.omg_format:                
                res[line.id] = line.location_id.omg_format
            else:
                res[line.id] = False
        return res
    
    _name = "omg.sale.reserve.contact.line.location"
    _description = "Location List of Contact"
    _columns = {
        'name': fields.char('Description', size=100),
        'contact_line_id': fields.many2one('omg.sale.reserve.contact.line', 'Lines', ondelete='cascade'),
        'location_id': fields.many2one('stock.location', 'Location', required=True, ondelete="restrict" ),
        'group_name': fields.function(_get_group, method=True, type='string', string="Group"),
#DAY-008
        'location_type_id': fields.related('location_id', 'location_type_id', type='many2one', relation='omg.sale.location.type', store=True, string='Type'),        
#DAY-009
        'specific_booth_type_id': fields.related('location_id','specific_booth_type_id', type='many2one',relation='omg.sale.location.booth.type', store=True, string='Booth Type'),
#DAY-011
        'omg_format': fields.function(_get_format, method=True, type='string', string="Format"),
        'estimate': fields.integer('Estimate * Days'),
        
    }
    _sql_constraints = [
        ('sale_reserve_line_location_uniq', 'unique (contact_line_id,location_id)', 'Location must be unique.')
    ]
    def unlink(self, cr, uid, ids, context=None, check=True):
        if context is None:
            context = {}
        for row in self.browse(cr, uid, ids):
            location_book_ids = self.pool.get('stock.location.booking').search(cr, uid, [('contact_line_id','=',row.contact_line_id.id),('location_id','=',row.location_id.id)])
            if location_book_ids:
                self.pool.get('stock.location.booking').unlink(cr, uid, location_book_ids)
        result = super(omg_sale_reserve_contact_line_location, self).unlink(cr, uid, ids, context)
        return result  
    
omg_sale_reserve_contact_line_location()

class omg_sale_reserve_contact_line_product(osv.osv):
    
    def _get_unitprice(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.product_id.list_price
        return res

    def _get_location_count(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            contact_line = self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, [line.contact_line_id.id])
            if contact_line:
                res[line.id] = contact_line[0].location_qty
            else:
                res[line.id] = 0
        return res

    def _get_day_count(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            contact_line = self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, [line.contact_line_id.id])
            if contact_line and contact_line[0].period_id:
                res[line.id] = contact_line[0].period_id.date_length
            else:
                res[line.id] = 0
        return res
    
    def _get_subtotal(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            product_qty = line.product_qty
            day_qty = line.day_qty
            location_qty = line.location_qty
            unit_price = line.sale_price
            res[line.id] =  int(product_qty) * int(day_qty or 0.0) * int(location_qty or 0.0) * unit_price
        return res

    _name = "omg.sale.reserve.contact.line.product"
    _description = "Product List of Contact"
    _columns = {
        'name': fields.char('Description', size=100),
        'contact_line_id': fields.many2one('omg.sale.reserve.contact.line', 'Lines', ondelete='cascade'),
        'product_id': fields.many2one('product.product', 'Products',required=True, ondelete="restrict" ),
        'product_qty': fields.integer('Quantity'),
        'unit_price': fields.function(_get_unitprice,method=True,type="float",string="Unit Price"),
        'sale_price': fields.float('Sale Price', digits_compute= dp.get_precision('Sale Price')),        
        'sub_total': fields.function(_get_subtotal,method=True,type="float",string="Total"),
        'sale_order_id': fields.many2one('sale.order','Sale Order', ondelete="restrict"),        
        'location_qty': fields.function(_get_location_count,method=True,type="integer",string="Location Count"),
        'day_qty': fields.function(_get_day_count,method=True,type="integer",string="Day Count"),      

    }
    _sql_constraints = [
        ('sale_reserve_line_product_uniq', 'unique (contact_line_id,product_id)', 'Product must be unique.')
    ]
    _defaults = {
        'product_qty': 1
    }
    
    def onchange_product_id(self, cr, uid, ids, product_id):
        v = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            v['sale_price'] = product.list_price
        return {'value': v}

    
omg_sale_reserve_contact_line_product()

class omg_sale_reserve_contact_line_summary(osv.osv):
    
    def _get_unitprice(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.product_id.list_price
        return res
    
    def _get_subtotal(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            location_qty = line.product_qty
            unit_price = line.sale_price
            #DAY-011
            if line.with_branch:
                branch = line.contact_line_id.location_qty
            else:
                branch = 1
            if line.with_period:
                period = line.contact_line_id.period_id.date_length
            else:
                period = 1
                       
            res[line.id] =  int(branch) * int(period) * int(location_qty) * unit_price or 0.0
        return res     
        
    _name = "omg.sale.reserve.contact.line.summary"
    _description = "Summary price of Contact"
    _columns = {
        'name': fields.char('Description', size=100),
        'contact_line_id': fields.many2one('omg.sale.reserve.contact.line', 'Lines', ondelete='cascade'),
        'product_id': fields.many2one('product.product', 'Products',required=True, ondelete="restrict" ),
        'product_qty': fields.integer('Quantity'),
        'unit_price': fields.function(_get_unitprice,method=True,type="float",string="Unit Price"),
        'sale_price': fields.float('Sale Price', digits_compute= dp.get_precision('Sale Price')),        
        'sub_total': fields.function(_get_subtotal,method=True,type="float",string="Total"),
        'sale_order_id': fields.many2one('sale.order','Sale Order', ondelete="restrict"),        
        #DAY-011
        'with_branch': fields.boolean('* Location'),
        'with_period': fields.boolean('* Days'),          
    }
    _sql_constraints = [
        ('sale_reserve_line_summary_uniq', 'unique (contact_line_id, product_id)', 'Product must be unique.')
    ]
    _defaults = {
        'product_qty': 1
    }
    def onchange_product_id(self, cr, uid, ids, product_id):
        v = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            v['sale_price'] = product.list_price
        return {'value': v}    
            
omg_sale_reserve_contact_line_summary()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
