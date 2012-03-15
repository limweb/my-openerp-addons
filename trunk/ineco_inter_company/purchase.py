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
from operator import itemgetter

class purchase_order(osv.osv):
    _name = "purchase.order"
    _inherit = "purchase.order"
    _description = "Export to NAV Class"
    _columns = {
        'nav_exported': fields.boolean('Exported'),
    }
    _defaults = {
        'nav_exported': False,
    }

    def schedule_export_nav(self, cr, uid, context=None):
        purchase_export_sql = """
            select id from purchase_order
            where nav_exported = False order by id
        """
        cr.execute(purchase_export_sql)
        export_ids = map(itemgetter(0), cr.fetchall())
        for row in export_ids:
            purchase_line_sql = """
                select
                  purchase_order.company_id as company_id, 
                  'Invoice' as document_type,
                  '' as buy_from_vendor_no,
                  purchase_order.name as purchase_no,
                  '' as pay_to_vendor_no,
                  '' as pay_to_contact,
                  purchase_order.date_order as order_date,
                  purchase_order.date_order as posting_date,
                  '' as payment_term_code,
                  '' as currency_code,
                  amount_total as price_include_vat,
                  '' as vendor_invoice_no,
                  '' as buy_from_contact,
                  to_char(now(), 'DD/MM/yyyy hh:mm:ss') as last_interfaced,
                  0 as line_no,
                  'G/L Account' as type,
                  '' as account_no,
                  purchase_order_line.name as description,
                  '' as description2,
                  purchase_order_line.product_qty as quantity,
                  purchase_order_line.price_unit as direct_unit_cost,
                  0 as line_discount,
                  '' as gen_posting_group,
                  '' as vat_posting_group,
                  '' as uom,
                  '' as wht_posting_group,
                  purchase_order.dimension_company as dimension_1,
                  purchase_order.dimension_department as dimension_2,
                  purchase_order.dimension_project as dimension_3,
                  purchase_order.dimension_product as dimension_4,
                  purchase_order.dimension_retailer as dimension_5,
                  purchase_order.dimension_customer as dimension_6
                from purchase_order_line
                left join purchase_order on purchase_order_line.order_id = purchase_order.id
                where 
                  purchase_order.nav_exported = False
                  and purchase_order.id = %s
                  and purchase_order_line.state <> 'cancel'            
                """
            cr.execute(purchase_line_sql % row)
            line_data =  cr.dictfetchall()
            if len(line_data):
                line_no = 1
                config_ids = self.pool.get('ineco.export.config').search(cr, uid, [('type','=','purchase'),('company_id','=',line_data[0]['company_id'])])
                config_obj = self.pool.get('ineco.export.config').browse(cr, uid, config_ids)      
                if config_obj:
                    config = config_obj[0]
                    path = config.path+"purchase-"+str(line_data[0]['company_id']) +"-"+str(row)+".csv"
                    f = open(path, 'wt')
                writer = csv.writer(f)
                for line in line_data:
                    if config_obj:      
                        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                        writer.writerow([
                            line['document_type'], 
                            line['buy_from_vendor_no'],  #NAV
                            line['purchase_no'], 
                            line['pay_to_vendor_no'],    #NAV
                            line['pay_to_contact'],      #Address ERP
                            line['order_date'], 
                            line['posting_date'], 
                            line['payment_term_code'], 
                            line['currency_code'],       #NAV
                            line['price_include_vat'], 
                            line['vendor_invoice_no'],    
                            line['buy_from_contact'],    #NAV
                            line['last_interfaced'],     #Address ERP
                            line_no, 
                            line['type'], 
                            line['account_no'],          #Account No ERP 
                            line['description'], 
                            line['description2'], 
                            line['quantity'], 
                            line['direct_unit_cost'], 
                            line['line_discount'], 
                            line['gen_posting_group'],   #NAV
                            line['vat_posting_group'],   #NAV
                            line['uom'], 
                            line['wht_posting_group'],   #NAV
                            line['dimension_1'], 
                            line['dimension_2'], 
                            line['dimension_3'], 
                            line['dimension_4'], 
                            line['dimension_5'], 
                            line['dimension_6'], 
                        ])
                        line_no += 1
            cr.execute("update purchase_order set nav_exported = True where id = %s " % row)
            #self.pool.get('purchase.order').write(cr, uid, [row], {'nav_exported': True})
        return True
        
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        vals.update({'nav_exported': False})
        return super(purchase_order, self).write(cr, uid, ids, vals, context=context)

purchase_order()