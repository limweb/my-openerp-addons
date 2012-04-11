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

class sale_order(osv.osv):
    _name = "sale.order"
    _description = "add dimension to sale order by nav"
    _inherit = "sale.order"
    _columns = {
        'dimension_company': fields.many2one('ineco.nav.dimension', "Company", ondelete="restrict"),
        'dimension_department': fields.many2one('ineco.nav.dimension', "Department", ondelete="restrict"),
        'dimension_project': fields.many2one('ineco.nav.dimension', "Project", ondelete="restrict"),
        'dimension_product': fields.many2one('ineco.nav.dimension', "Product", ondelete="restrict"),
        'dimension_retailer': fields.many2one('ineco.nav.dimension', "Retailer", ondelete="restrict"),
        'dimension_customer': fields.many2one('ineco.nav.dimension', "Customer", ondelete="restrict"),
    }
    
    def schedule_export_store(self, cr, uid, context=None):
        if context is None:
            context = {}
        if date_invoice is None:
            date_invoice = time.strftime('%Y-%m-%d')
        query = """
                select c.name as sale_no, a.id as id, b.name as store_name from sale_branch_line a
                join stock_location b on a.location_id = b.id
                join sale_order c on a.sale_id = c.id
                join account_invoice d on d.origin = c.name
                where to_char(d.date_invoice, 'yyyy-mm-dd') = '%s'       
        """
        cr.execute(query % date_invoice)
        line_data =  cr.dictfetchall()
        if line_data:
            config_ids = self.pool.get('ineco.export.config').search(cr, uid, [('type','=','store')])
            config_obj = self.pool.get('ineco.export.config').browse(cr, uid, config_ids)      
            if config_obj:
                config = config_obj[0]
                path = config.path+"STORE-"+str(date_invoice)+".csv"
                #POP-001
                f = open(path, 'wt')
                #f = codecs.open(path, encoding='cp874', mode='w+')
                writer = csv.writer(f)
                for line in line_data:
                    if config_obj:      
                        writer = csv.writer(f, quoting=csv.QUOTE_NONE) # QUOTE_NONNUMERIC
                        writer.writerow([
                            line['sale_no'],
                            line['id'],
                            line['store_name'], 
                        ])

sale_order()