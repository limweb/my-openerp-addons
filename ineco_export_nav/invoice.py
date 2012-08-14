# -*- coding: utf-8 -*-
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
##############################################################################

# Date             ID         Message
# 21-12-2011       POP-001    Change file type to cp874 (support window)

import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp

import netsvc
import csv
import time
import codecs

from operator import itemgetter

import pymssql

class account_invoice(osv.osv):
    
    _name = "account.invoice"
    _description = "Add Dimension"
    _inherit = "account.invoice"
    _columns = {
        'nav_exported': fields.boolean('Exported'),
    }
    _defaults = {
        'nav_exported': False,
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        vals.update({'nav_exported': False})
        return super(account_invoice, self).write(cr, uid, ids, vals, context=context)

    def schedule_export_supplier_invoice(self, cr, uid, context=None):
        purchase_export_sql = """
            select id from account_invoice
            where nav_exported = False and type = 'in_invoice' order by id
        """
        cr.execute(purchase_export_sql)
        export_ids = map(itemgetter(0), cr.fetchall())
        for row in export_ids:
            purchase_line_sql = """
               select 
                  account_invoice.company_id as company_id,
                  'Invoice' as document_type,
                  res_partner.ref as buy_from_vendor_no,
                  account_invoice.origin as purchase_no,
                  res_partner.ref as pay_to_vendor_no,
                  coalesce(res_partner_address.name,'') as pay_to_contact,
                  to_char(CURRENT_DATE,'DD/MM/yyyy') as order_date,
                  to_char(CURRENT_DATE,'DD/MM/yyyy') as posting_date,
                  account_payment_term.code_nav as payment_term_code, --payment_term (int)
                  '' as currency_code,     --currency_id (int)
                  'Yes' as price_include_vat, --account_invoice.amount_total as
                  '' as vendor_invoice_no,
                  coalesce(address2.name,'') as buy_from_contact,
                  to_char(now(), 'DD/MM/yyyy HH:mm:ss') as last_interfaced,
                  'G/L Account' as nav_type,
                  account_account.code as account_no,
                  replace(account_invoice_line.name,'"','') as description,
                  replace(account_invoice_line.name,'"','') as description2,
                  account_invoice_line.quantity as quantity,
                  account_invoice_line.price_unit as direct_unit_cost,
                  account_invoice_line.discount as line_discount,
                  post1.code_nav as gen_posting_group,
                  post2.code_nav as vat_posting_group,
                  '' as uom,
                  post3.code_nav as wht_posting_group,
                  d1.code  as dimension_1,
                  d2.code as dimension_2,
                  d3.code as dimension_3,
                  d4.code as dimension_4,
                  d5.code as dimension_5,
                  d6.code as dimension_6,
                  account_invoice.id as invoice_id
                from account_invoice_line
                join account_invoice on account_invoice_line.invoice_id = account_invoice.id
                left join res_partner_address          on account_invoice.address_invoice_id = res_partner_address.id
                left join res_partner_address address2 on account_invoice.address_contact_id = address2.id
                left join account_account on account_invoice_line.account_id = account_account.id
                left join purchase_order on purchase_order.name = account_invoice.origin
                left join res_partner on account_invoice.partner_id = res_partner.id
                left join account_payment_term on account_invoice.payment_term = account_payment_term.id
                left join ineco_nav_postmaster post1 on res_partner.gen_bus_posting_group_id = post1.id
                left join ineco_nav_postmaster post2 on res_partner.vat_bus_posting_group_id = post2.id
                left join ineco_nav_postmaster post3 on res_partner.wht_bus_posting_group_id = post3.id                
                left join ineco_nav_dimension d1 on purchase_order.dimension_company = d1.id
                left join ineco_nav_dimension d2 on purchase_order.dimension_department = d2.id
                left join ineco_nav_dimension d3 on purchase_order.dimension_project = d3.id
                left join ineco_nav_dimension d4 on purchase_order.dimension_product = d4.id
                left join ineco_nav_dimension d5 on purchase_order.dimension_retailer = d5.id
                left join ineco_nav_dimension d6 on purchase_order.dimension_customer = d6.id
                where 
                  account_invoice.type = 'in_invoice' --supplier invoice
                  and account_invoice.nav_exported = False
                  and account_invoice.id = %s           
                """
            cr.execute(purchase_line_sql % row)
            line_data =  cr.dictfetchall()
            if len(line_data):
                line_no = 1
                config_ids = self.pool.get('ineco.export.config').search(cr, uid, [('type','=','purchase'),('company_id','=',line_data[0]['company_id'])])
                config_obj = self.pool.get('ineco.export.config').browse(cr, uid, config_ids)      
                if config_obj:
                    config = config_obj[0]
                    path = config.path+"PI-"+str(line_data[0]['company_id']) +"-"+str(row)+".csv"
                    #POP-001
                    f = open(path, 'wt')
                    #f = codecs.open(path, encoding='cp874', mode='w+')
                    writer = csv.writer(f)
                for line in line_data:
                    if config_obj:      
                        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                        try:
                            writer.writerow([
                                line['document_type'], 
                                line['buy_from_vendor_no'].encode('cp874'),  #NAV
                                line['purchase_no'], 
                                line['pay_to_vendor_no'].encode('cp874'),    #NAV
                                line['pay_to_contact'].encode('cp874'),      #Address ERP
                                line['order_date'], #required gen date of erp
                                line['posting_date'], 
                                line['payment_term_code'], 
                                line['currency_code'],       #NAV
                                line['price_include_vat'] or 'Yes', #NAV Vat Type (include,exclude) (Yes,No)
                                line['vendor_invoice_no'],    
                                line['buy_from_contact'].encode('cp874'),    #NAV
                                line['last_interfaced'],     #Address ERP
                                line_no, 
                                line['nav_type'], 
                                line['account_no'],          #Account No ERP 
                                line['description'][0:50].encode('cp874'), 
                                line['description2'][50:0].encode('cp874'), 
                                line['quantity'], 
                                line['direct_unit_cost'], 
                                line['line_discount'], 
                                line['gen_posting_group'] ,    #NAV Generate from Gen. Product Posting Group
                                line['vat_posting_group'] ,   #NAV
                                line['uom'], 
                                line['wht_posting_group'] ,   #NAV
                                line['dimension_1'], 
                                line['dimension_2'], 
                                line['dimension_3'], 
                                line['dimension_4'], 
                                line['dimension_5'], 
                                #line['dimension_6'], 
                            ])
                        except Exception, err:
                            self.log(cr, uid, line['invoice_id'], 'Export Error -> '+line['purchase_no']+":"+str(err))
                            pass
                        line_no += 1
                if config_obj:
                    cr.execute("update account_invoice set nav_exported = True where id = %s " % row)
            #self.pool.get('purchase.order').write(cr, uid, [row], {'nav_exported': True})
        return True

    def schedule_export_customer_invoice(self, cr, uid, context=None):
        purchase_export_sql = """
            select id from account_invoice
            where nav_exported = False and type = 'out_invoice' order by id
        """
        cr.execute(purchase_export_sql)
        export_ids = map(itemgetter(0), cr.fetchall())
        for row in export_ids:
            purchase_line_sql = """
                select 
                  account_invoice.company_id as company_id,
                  'Invoice' as document_type,
                  res_partner.ref as buy_from_vendor_no,
                  account_invoice.origin as purchase_no,
                  res_partner.ref as pay_to_vendor_no,
                  coalesce(res_partner_address.name,'') as pay_to_contact,
                  to_char(account_invoice.date_invoice, 'DD/MM/yyyy') as order_date,
                  to_char(account_invoice.date_invoice,'DD/MM/yyyy') as posting_date ,
                  account_payment_term.code_nav as payment_term_code, --payment_term (int)
                  '' as currency_code,     --currency_id (int)
                  account_invoice.amount_total as price_include_vat,
                  '' as vendor_invoice_no,
                  coalesce(address2.name,'') as buy_from_contact,
                  to_char(now(), 'DD/MM/yyyy HH:mm') as last_interfaced,
                  'G/L Account' as nav_type,
                  account_account.code as account_no,
                  account_invoice_line.name as description,
                  '' as description2,
                  account_invoice_line.quantity as quantity,
                  account_invoice_line.price_unit as direct_unit_cost,
                  account_invoice_line.discount as line_discount,
                  post1.code_nav as gen_posting_group,
                  post2.code_nav as vat_posting_group,
                  '' as uom,
                  post3.code_nav as wht_posting_group,
                  d1.code  as dimension_1,
                  d2.code as dimension_2,
                  d3.code as dimension_3,
                  d4.code as dimension_4,
                  d5.code as dimension_5,
                  d6.code as dimension_6,
                  account_invoice.name as contact_no,
                  account_invoice.id as invoice_id,
                  '' as taxcoding,
                  to_char(sale_order.date_period_start,'dd/mm/yyyy') || ' - ' || to_char(sale_order.date_period_finish,'dd/mm/yyyy') as cycle_name,
                  sale_order.date_period_finish - sale_order.date_period_start + 1 as cycle_day,
                  pcserv.name as service_category_name,
                  pcustomer.name as customer_product_name,
                  '' as customer_po
                from account_invoice_line
                join account_invoice on account_invoice_line.invoice_id = account_invoice.id
                left join res_partner_address          on account_invoice.address_invoice_id = res_partner_address.id
                left join res_partner_address address2 on account_invoice.address_contact_id = address2.id
                left join account_account on account_invoice_line.account_id = account_account.id
                left join sale_order on sale_order.name = account_invoice.origin
                left join res_partner on account_invoice.partner_id = res_partner.id
                left join account_payment_term on account_invoice.payment_term = account_payment_term.id
                left join ineco_nav_postmaster post1 on res_partner.gen_bus_posting_group_id = post1.id
                left join ineco_nav_postmaster post2 on res_partner.vat_bus_posting_group_id = post2.id
                left join ineco_nav_postmaster post3 on res_partner.wht_bus_posting_group_id = post3.id                
                left join ineco_nav_dimension d1 on sale_order.dimension_company = d1.id
                left join ineco_nav_dimension d2 on sale_order.dimension_department = d2.id
                left join ineco_nav_dimension d3 on sale_order.dimension_project = d3.id
                left join ineco_nav_dimension d4 on sale_order.dimension_product = d4.id
                left join ineco_nav_dimension d5 on sale_order.dimension_retailer = d5.id
                left join ineco_nav_dimension d6 on sale_order.dimension_customer = d6.id  
                left join product_template pserv on sale_order.service_product_id = pserv.id 
                left join product_category pcserv on pserv.categ_id = pcserv.id       
                left join product_template pcustomer on sale_order.customer_product_id = pcustomer.id     
                where 
                  account_invoice.type = 'out_invoice' --supplier invoice
                  and account_invoice.nav_exported = False                 
                  and account_invoice.id = %s           
                """
            cr.execute(purchase_line_sql % row)
            line_data =  cr.dictfetchall()
            if len(line_data):
                line_no = 1
                config_ids = self.pool.get('ineco.export.config').search(cr, uid, [('type','=','sale'),('company_id','=',line_data[0]['company_id'])])
                config_obj = self.pool.get('ineco.export.config').browse(cr, uid, config_ids)      
                if config_obj:
                    config = config_obj[0]
                    path = config.path+"SALESINV-"+str(line_data[0]['company_id']) +"-"+str(row)+".csv"
                    #POP-001
                    f = open(path, 'wt')
                    #f = codecs.open(path, encoding='cp874', mode='w+')
                    writer = csv.writer(f)
                for line in line_data:
                    if config_obj:      
                        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                        try:
                            writer.writerow([
                                line['document_type'], 
                                line['buy_from_vendor_no'].encode('cp874'),  #NAV
                                line['purchase_no'], 
                                line['pay_to_vendor_no'].encode('cp874'),    #NAV
                                line['pay_to_contact'].encode('cp874') or '',      #Address ERP
                                line['posting_date'], #ERP Generate Curredimension_6nt Date Post
                                line['payment_term_code'],   #NAV
                                line['currency_code'],       #NAV
                                'No' ,  #line['price_include_vat'],   #Boolean Yes/No
                                'S001' , #Add Nav Sale ID
                                line['buy_from_contact'].encode('cp874'),    #NAV
                                line['last_interfaced'],     #Address ERP
                                line_no, 
                                line['nav_type'], 
                                line['account_no'],          #Account No ERP 
                                line['description'][0:50].encode('cp874'), 
                                line['description2'][50:0].encode('cp874'), 
                                line['quantity'], 
                                line['uom'], 
                                line['direct_unit_cost'],                             
                                line['line_discount'], 
                                line['gen_posting_group'] or '',    #NAV
                                line['vat_posting_group'] or '', #NAV REQUERY from master product
                                line['wht_posting_group'] or '',    #NAV or '' ว่าง
                                line['contact_no'] or '',
                                line['dimension_1'], 
                                line['dimension_2'], 
                                line['dimension_3'], 
                                line['dimension_4'], 
                                line['dimension_5'], 
                                line['dimension_6'], 
                                line['taxcoding'] or '', 
                                line['service_category_name'] or '', 
                                line['cycle_name'] or '', 
                                line['customer_product_name'] or '', 
                                line['cycle_day'], 
                                line['customer_po'] or '', 
                            ])
                        except Exception, err:
                            self.log(cr, uid, line['invoice_id'], 'Export Error -> '+line['purchase_no']+":"+str(err))
                            pass
                    line_no += 1
                if config_obj:
                    cr.execute("update account_invoice set nav_exported = True where id = %s " % row)
            #self.pool.get('purchase.order').write(cr, uid, [row], {'nav_exported': True})
        return True
    
account_invoice()