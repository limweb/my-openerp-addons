# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 INECO PARTNERSHIP LIMITED (<http://openerp.tititab.com>).
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
from osv import fields, osv
from osv.orm import browse_record, browse_null
from tools.translate import _

class contact_merge_wizard(osv.osv_memory):
    
    _name = "contact.merge.wizard"
    _description = "Wizard to create Sale Order from sale contact."
    _columns = {
    }

    def do_merge(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record_ids = context and context.get('active_ids', False)
        user_id = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        shop_ids = self.pool.get('sale.shop').search(cr, uid, [('company_id','=',user_id.company_id.id)])
        shop_id = self.pool.get('sale.shop').browse(cr, uid, shop_ids)[0]
        for record_id in record_ids:
            can_do = True

            for contact in self.pool.get('omg.sale.reserve.contact').browse(cr, uid, [record_id]):
                for contact_line in contact.line_ids:
                    if can_do:
                        can_do = contact_line._check_booking
            if not can_do:
                raise osv.except_osv(_('Warning'), _('Some line can not be booking.')) 
            
            if can_do:
                #disable chain_id
                cr.execute("select distinct chain_id, period_id from omg_sale_reserve_contact_line where contact_id = "+str(record_id) )
                #cr.execute("select distinct period_id from omg_sale_reserve_contact_line where contact_id = "+str(record_id) )
                for res in cr.dictfetchall(): 
                    contact = self.pool.get('omg.sale.reserve.contact').browse(cr, uid, [record_id])[0]
                    #disable chain_id
                    cr.execute("select id from omg_sale_reserve_contact_line where chain_id = %s and period_id = %s and contact_id = %s and state not in ('done','cancel')", 
                               (str(res['chain_id']),str(res['period_id']), str(record_id)))
                    #cr.execute("select id from omg_sale_reserve_contact_line where period_id = %s and state not in ('done','cancel')"  
                    #           % str(res['period_id']))
                    line_ids = map(lambda x: x[0], cr.fetchall())
                    if not line_ids: 
                        continue
                    sale_order_obj = self.pool.get('sale.order')
                    sale_order_id = sale_order_obj.create(cr, uid, {
                        'pricelist_id': contact.customer_id.property_product_pricelist.id,
                        'date_order': time.strftime('%Y-%m-%d'),
                        'client_order_ref': contact.name,
                        'customer_product_id': contact.product_id.id,
                        'user_id': contact.saleman_id.id or False,
                        'partner_id': contact.customer_id.id,        
                        'partner_order_id': contact.customer_id.address[0].id,    
                        'partner_invoice_id': contact.customer_id.address[0].id,    
                        'partner_shipping_id': contact.customer_id.address[0].id,    
                        'shop_id': shop_id.id,
                        'company_id': contact.company_id.id,
                    })
                    sale_branch_obj = self.pool.get('sale.branch.line')
                    #line_obj = self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, line_ids)[0]
                    for line_obj in self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, line_ids):
                        line_obj.allow = line_obj.allow_duplicate
        
                        for location in line_obj.location_lines:
                            if line_obj._can_booking(location.location_id.id, line_obj.category_id.id, line_obj.period_id.id ):
                                sale_branch_obj.create(cr,uid,{
                                    'sale_id': sale_order_id,
                                    'location_id': location.location_id.id,
                                    'location_name': location.location_id.name,
                                    'group': location.location_id.location_group_id.name or False,
                                    'department': location.location_id.chain_id.name or False,
                                    'area': location.location_id.location_type_id.name or False
                                })
                            
                    sale_period_line_obj = self.pool.get('sale.period.line')
                    sale_period_line_obj.create(cr, uid, {
                        'period_id': line_obj.period_id.id,
                        'sale_id': sale_order_id,
                        'description': line_obj.period_id.name,
                        'date_start': line_obj.period_id.date_start,
                        'date_finish' : line_obj.period_id.date_finish,
                    })
                    fpos = False
                    client_price = 0
                    for line_obj in self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, line_ids):
                        client_price = line_obj.client_price
                    sale_order_line_obj = self.pool.get('sale.order.line')
                    sale_order_line_obj.create(cr, uid, {
                        'order_id': sale_order_id,
                        'product_id': contact.service_id.id,
                        'name': contact.service_id.name,
                        'product_uom': contact.service_id.uom_id.id,
                        'product_uom_qty': 1,
                        'price_unit': client_price or contact.service_id.list_price , #contact_obj.unit_price,
                        'tax_id': [(6, 0, [x.id for x in contact.service_id.taxes_id])],
                        'with_branch': True,
                        'with_period': True,                        
                    })        
    
                    for line_out in self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, line_ids):
                        for product in line_out.product_lines:
                            sale_order_line_obj.create(cr, uid, {
                                'order_id': sale_order_id,
                                'product_id': product.product_id.id,
                                'name': product.product_id.name,
                                'product_uom': product.product_id.uom_id.id,
                                'product_uom_qty': product.product_qty,
                                'price_unit': 0 or product.sale_price ,
                                'with_branch': True,
                                'with_period': True,
                                'tax_id': [(6, 0, [x.id for x in product.product_id.taxes_id])] ,
                            })
    
                        for product in line_out.summary_lines:
                            sale_order_line_obj.create(cr, uid, {
                                'order_id': sale_order_id,
                                'product_id': product.product_id.id,
                                'name': product.product_id.name,
                                'product_uom': product.product_id.uom_id.id,
                                'product_uom_qty': product.product_qty,
                                'price_unit': product.sale_price ,
                                'with_branch': False,
                                'with_period': False,
                                'tax_id': [(6, 0, [x.id for x in product.product_id.taxes_id])] ,
                            })
    
    #                location_book_ids = self.pool.get('stock.location.booking').search(cr, uid, [('contact_line_id','=',ids[0])])
                    for line_obj in self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, line_ids):      
                        location_book_ids = self.pool.get('stock.location.booking').search(cr, uid,
                                 [('period_id','=',line_obj.period_id.id),('chain_id','=',line_obj.chain_id.id)])
                        if location_book_ids:
                            for booking in self.pool.get('stock.location.booking').browse(cr, uid, location_book_ids):
                                booking.write({'state':'done','order_id':sale_order_id})
    
                    for line_out in self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, line_ids):
                        line_out.write({'state':'done','sale_order_id':sale_order_id})
                        for location in line_out.location_lines:
                            line_out._make_cancel(location.location_id.id, line_out.category_id.id, line_out.period_id.id )
                
            #for res in cr.dictfetchall():
                #res['chain_id'],
                #res['period_id']
        return {'type': 'ir.actions.act_window_close'}

contact_merge_wizard()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
