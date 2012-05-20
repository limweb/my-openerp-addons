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

import pymssql

from datetime import *

class sale_order(osv.osv):
    _name = "sale.order"
    _description = "export to fos only"
    _inherit = "sale.order"
    _columns = {
    }
    
    def export_fos(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for order in self.pool.get('sale.order').browse(cr, uid, ids):
            sql = """
                select 
                  substring(client_order_ref,1,23) as bookingno,
                  substring(so.name,1,23) as contractno,
                  'DEMO' as contrpointcd, 
                  'N' as status,
                  substring(rp.name,1,100) as company1,
                  substring(rpa.name,1,100) as contact1,
                  substring(rpa.phone,1,30) as tel1,
                  substring(rpa.fax,1,30) as fax1,
                  substring(rp.name,1,100) as marketercd,
                  substring(rp.name,1,100) as mktcompany2,
                  substring(rpa.name,1,100) as mktcontact2,
                  substring(rpa.phone,1,30) as mkttel2,
                  substring(rpa.fax,1,30) as mktfax2,
                  osrc.contact_date::date as bookdt,
                  so.date_confirm::date as confirmdt,
                  so.date_order::date as contractdt,
                  osp.date_start::date as demostr,
                  osp.date_finish::date as demoend,
                  substring(ru2.login,1,10) as bookby, --'wait change - osrc.sale_admin_id' as bookby,
                  substring(ru.login,1,10) as contrby, --'wait change - osrc.saleman_id' as contrby,
                  substring(ru.name,1,50) as contrname,
                  (select count(*) from sale_branch_line where sale_id = so.id)  as nostore,
                  (select count(*) from sale_branch_line sbl 
                left join stock_location sl on sl.id = sbl.location_id
                left join omg_sale_location_type oslt on sl.location_type_id = oslt.id
                where oslt.name = 'BKK' and sale_id = so.id) as nostorebkk,
                  (select count(*) from sale_branch_line where sale_id = so.id)  -
                  (select count(*) from sale_branch_line sbl 
                left join stock_location sl on sl.id = sbl.location_id
                left join omg_sale_location_type oslt on sl.location_type_id = oslt.id
                where oslt.name = 'BKK' and sale_id = so.id) as  nostoreupc,
                  osp.date_finish - osp.date_start as nodemodays,
                (select sum(sm.product_qty) from stock_picking sp
                left join stock_move sm on sm.picking_id = sp.id
                left join product_product pp on sm.product_id = pp.id
                left join ineco_stock_sticker_category issc on pp.sticker_category_id = issc.id
                where type = 'out' and issc.name = 'Pretty' and sm.state <> 'cancel' and sp.sale_id = so.id) as noofprogirl, -- 'wait change' as noofprogirl,
                  substring(pc3.name,1,20) as categorycd,
                  substring(pc2.name,1,25) as subcatcd,
                  substring(pp.name_template,1,100) as brandcd,
                  substring(pp.name_template,1,200) as productdesc,
                  pc.id as boothcd,
                  to_char(osp.date_start, 'yyyy') as year,
                  to_char(osp.date_start, 'Q') as quarter,
                  to_char(osp.date_start, 'MM') as mth,
                  SUBSTRING(ospc.name, 'Y*([0-9]{1,})')::Integer as weekno,-- 'wait change' as weekno,
                  osc.name as chaincd, --'wait change - osrc.chain_id' as chaincd,
                  amount_untaxed as totdemochg,
                  amount_untaxed as totsubamt,
                  amount_tax as tottaxamt,
                  amount_total as totnetamtdue,
                  0 as noofholiday,
                  (osp.date_finish - osp.date_start ) + 1 as noofworkday, --'wait change' as noofworkday,
                  'F' as oneway,
                  'T' as twoway,
                  3 as dlvsystem, 
                  'Y' as flagworkday,
                  ru3.login as usercreate,
                  so.create_date::date as createdate
                from sale_order so
                left join res_partner rp on so.partner_id = rp.id
                left join res_partner_address rpa on so.partner_order_id = rpa.id
                left join omg_sale_reserve_contact osrc on so.client_order_ref = osrc.name
                left join omg_sale_period osp on so.period_id = osp.id
                left join product_product pp on so.customer_product_id = pp.id
                left join product_category pc on so.service_category_id = pc.id
                left join product_category pc3 on pc.parent_id = pc3.id
                left join product_template pt on pp.product_tmpl_id = pt.id
                left join product_category pc2 on pt.categ_id = pc2.id
                left join res_users ru on osrc.saleman_id = ru.id
                left join res_users ru2 on osrc.sale_admin_id = ru2.id
                left join omg_sale_chain osc on osrc.chain_id = osc.id
                left join res_users ru3 on so.create_uid = ru3.id
                left join omg_sale_period_category ospc on ospc.id = osp.category_id
                where so.company_id = %s and so.id = %s           
            """
            cr.execute(sql % (order.company_id.id, order.id))
            line_data =  cr.dictfetchall()
            for data in line_data:
                insert_field = self._genfield(data,1);
                insert_value = self._genfield(data,2);
                insert_contrmf_sql = 'insert into contrmf '+insert_field+' values '+insert_value
                if order.company_id.fos_host and order.company_id.fos_user and order.company_id.fos_dbname:
                    server_ip = order.company_id.fos_host
                    server_user = order.company_id.fos_user
                    server_password = order.company_id.fos_password
                    server_db = order.company_id.fos_dbname
                    conn = pymssql.connect(host=server_ip, user=server_user, password=server_password, 
                                           database=server_db,as_dict=True)
                    cur = conn.cursor()
                    cur.execute(insert_contrmf_sql)
                    
                    #sql_complete = sql % (company.ineco_nav_table,table_name) 
                    ##cur.execute(sql_complete )
                    
                else:
                    raise osv.except_osv(_('Error !'), _('Please config FOS Server in company.'))
        return True
    
    def _genfield(self, data, sqltype):
        #sqltype : 1 -> insert fields
        #        : 2 -> insert values
        #        : 3 -> set values
        
        result = ""
        for key in data.iterkeys():
            if (sqltype == 1):
                result = result+key+','
            elif (sqltype == 2):
                if data[key] == False:
                    result = result+"null,"
                else:
                    if isinstance(data[key], (str,unicode,date,datetime)):
                        result = result+"'%s'," % data[key]
                    else:
                        result = result+"%s," % data[key]
            elif (sqltype == 3):
                if data[key] == False:
                    result = result+key+"=null, "
                else: 
                    if isinstance(data[key], (str,unicode,date,datetime)):
                        result = result+key+"='%s', " % data[key]
                    else:
                        result = result+key+"=%s, " % data[key]   
        if (sqltype == 1):
            result = '('+result[0:len(result)-1]+')'
        elif (sqltype == 2):
            result = '('+result[0:len(result)-1]+')'
        elif (sqltype == 3):
            result = result[0:len(result)-2]
        result = result.replace('None','null') 
        return result 
sale_order()