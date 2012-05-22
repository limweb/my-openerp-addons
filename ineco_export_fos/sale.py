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
import codecs

import pymssql
import _mssql

from datetime import *

class sale_order(osv.osv):
    _name = "sale.order"
    _description = "export to fos only"
    _inherit = "sale.order"
    _columns = {
    }
    
    def testmethod(self, cr, uid, ip, user, database, password, context=None):
        server_ip = ip
        server_user = user
        server_password = password
        server_db = database

        conn = _mssql.connect(server=server_ip, user=server_user, password=server_password, 
                               database=server_db)
        #cur = conn.cursor()
        
        sql = "select * from storemf"
        conn.execute_query(sql)
        #datas = cur.fetchall()
        for row in conn:
            print "ID=%d, Name=%s" % (row['chaincd'], row['storecd'])

        return true
    
    def export_fos(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
            
        for order in self.pool.get('sale.order').browse(cr, uid, ids):
            
            sql = """
                select 
                  substring(client_order_ref,1,23) as bookingno,
                  substring(so.name,1,23) as contractno,
                  'DEMO' as contrpointcd, 
                  'C' as status,
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
                  ((osp.date_finish - osp.date_start) + 1) * (select count(*) from sale_branch_line where sale_id = so.id) as nodemodays,
                (select sum(sm.product_qty) from stock_picking sp
                left join stock_move sm on sm.picking_id = sp.id
                left join product_product pp on sm.product_id = pp.id
                left join ineco_stock_sticker_category issc on pp.sticker_category_id = issc.id
                where type = 'out' and issc.name = 'Pretty' and sm.state <> 'cancel' and sp.sale_id = so.id) as noofprogirl, -- 'wait change' as noofprogirl,
                  'ERP Category' as categorycd,
                  substring(pc2.name,1,25) as subcatcd,
                  substring(pp.name_template,1,100) as brandcd,
                  substring(pp.name_template,1,200) as productdesc,
                  1 as boothcd,
                  to_char(osp.date_start, 'yyyy') as year,
                  to_char(osp.date_start, 'Q') as quarter,
                  to_char(osp.date_start, 'MM') as mth,
                  SUBSTRING(ospc.name, 'Y*([0-9]{1,})')::Integer as weekno,-- 'wait change' as weekno,
                  substring(osc.name,1,15) as chaincd, --'wait change - osrc.chain_id' as chaincd,
                  amount_untaxed as totdemochg,
                  amount_untaxed as totsubamt,
                  amount_tax as tottaxamt,
                  amount_total as totnetamtdue,
                  0 as noofholiday,
                  (osp.date_finish - osp.date_start ) + 1 as noofworkday, --'wait change' as noofworkday,
                  '' as oneway,
                  '' as twoway,
                  3 as dlvsystem, 
                  'Y' as flagworkday,
                  substring(ru3.login,1,10) as usercreate,
                  so.create_date::date as createdate,
                  'D' as typeserv,  --New Field In Master Product by FOS
                  7 as taxrate
                  
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
                self.testmethod(cr, uid, order.company_id.fos_host, order.company_id.fos_user, order.company_id.fos_dbname, order.company_id.fos_password)
                insert_field = self._genfield(data,1);
                insert_value = self._genfield(data,2);
                insert_contrmf_sql = 'insert into contrmf '+insert_field+' values '+insert_value
                update_contrmf_sql = "update contrmf set "+self._genfield(data,3)+" where contractno = '%s'" % data['contractno']
                if order.company_id.fos_host and order.company_id.fos_user and order.company_id.fos_dbname:
                    server_ip = order.company_id.fos_host
                    server_user = order.company_id.fos_user
                    server_password = order.company_id.fos_password
                    server_db = order.company_id.fos_dbname

                    conn = pymssql.connect(host=server_ip, user=server_user, password=server_password, 
                                           database=server_db,as_dict=True)
                    cur = conn.cursor()
                    try:
                        #insert_sql
                        cur.execute('SET ANSI_WARNINGS off')
                        cur.execute(insert_contrmf_sql.encode('cp874'))

                    except:
                        #update_sql
                        cur.execute('SET ANSI_WARNINGS off')
                        cur.execute(update_contrmf_sql.encode('cp874'))

                    cur.close()
                    conn.commit()
                    
                else:
                    raise osv.except_osv(_('Error !'), _('Please config FOS Server in company.'))
                
            salescalendar_sql = """
                select
                  osc.name as chaincd, --'wait change - osrc.chain_id' as chaincd,
                  to_char(osp.date_start, 'yyyy') as year,
                  SUBSTRING(ospc.name, 'Y*([0-9]{1,})')::Integer as weekno,-- 'wait change' as weekno,
                  pc.id as boothcd, 
                  client_order_ref as bookingno,
                  so.name as contractno,
                  sl.store_code as storecd,
                  sl.name as storename,
                  oslg.name as groupcd,
                  'Y' as wascontract,
                  'N' as wascancel
                from sale_order so
                join sale_branch_line sbl on sbl.sale_id = so.id
                join stock_location sl on sbl.location_id = sl.id
                join omg_sale_location_group oslg on sl.location_group_id = oslg.id
                 join omg_sale_reserve_contact osrc on so.client_order_ref = osrc.name
                 join omg_sale_period osp on so.period_id = osp.id
                left join product_category pc on so.service_category_id = pc.id
                 join omg_sale_chain osc on osrc.chain_id = osc.id
                 join res_users ru3 on so.create_uid = ru3.id
                 join omg_sale_period_category ospc on ospc.id = osp.category_id
                where so.company_id = %s and so.id = %s
            """
            cr.execute(salescalendar_sql % (order.company_id.id, order.id))
            line_data =  cr.dictfetchall()
            for data in line_data:
                insert_field = self._genfield(data,1);
                insert_value = self._genfield(data,2);
                insert_contrmf_sql = 'insert into salescalendar '+insert_field+' values '+insert_value
                update_contrmf_sql = "update salescalendar set "+self._genfield(data,3)+" where contractno = '%s' and storecd = '%s' " % ( data['contractno'], data['storecd'])
                if order.company_id.fos_host and order.company_id.fos_user and order.company_id.fos_dbname:
                    server_ip = order.company_id.fos_host
                    server_user = order.company_id.fos_user
                    server_password = order.company_id.fos_password
                    server_db = order.company_id.fos_dbname

                    conn = pymssql.connect(host=server_ip, user=server_user, password=server_password, 
                                           database=server_db,as_dict=True)
                    cur = conn.cursor()
                    try:
                        #insert_sql
                        cur.execute('SET ANSI_WARNINGS off')
                        cur.execute(insert_contrmf_sql.encode('cp874'))

                    except:
                        #update_sql
                        cur.execute('SET ANSI_WARNINGS off')
                        cur.execute(update_contrmf_sql.encode('cp874'))

                    cur.close()
                    conn.commit()
                    
                else:
                    raise osv.except_osv(_('Error !'), _('Please config FOS Server in company.'))

            costitem_sql = """
                select
                  so.name as contractno,
                  so.client_order_ref as bookingno,
                  pp.id as costitem,
                  1 as lineseq,
                  'other' as typecd,
                  pp.name_template as costdesc,
                  product_uom_qty as chargeqty,
                  'Day' as chargeuom,
                  (select count(*) from sale_branch_line where sale_id = so.id) as altqty ,
                  'Store' as altuom,
                  coalesce(price_unit,0) as chargerate
                from 
                  sale_order so 
                join sale_order_line sol on so.id = sol.order_id
                left join omg_sale_reserve_contact osrc on so.client_order_ref = osrc.name
                left join product_product pp on sol.product_id = pp.id
               where so.company_id = %s and so.id = %s
            """
            cr.execute(costitem_sql % (order.company_id.id, order.id))
            line_data =  cr.dictfetchall()
            for data in line_data:
                insert_field = self._genfield(data,1);
                insert_value = self._genfield(data,2);
                insert_contrmf_sql = 'insert into contr_costitem '+insert_field+' values '+insert_value
                update_contrmf_sql = "update contr_costitem set "+self._genfield(data,3)+" where contractno = '%s' and costitem = %s " % (data['contractno'],data['costitem'])
                if order.company_id.fos_host and order.company_id.fos_user and order.company_id.fos_dbname:
                    server_ip = order.company_id.fos_host
                    server_user = order.company_id.fos_user
                    server_password = order.company_id.fos_password
                    server_db = order.company_id.fos_dbname

                    conn = pymssql.connect(host=server_ip, user=server_user, password=server_password, 
                                           database=server_db,as_dict=True)
                    cur = conn.cursor()
                    try:
                        #insert_sql
                        cur.execute('SET ANSI_WARNINGS off')
                        cur.execute(insert_contrmf_sql.encode('cp874'))

                    except:
                        #update_sql
                        cur.execute('SET ANSI_WARNINGS off')
                        cur.execute(update_contrmf_sql.encode('cp874'))

                    cur.close()
                    conn.commit()
                    
                else:
                    raise osv.except_osv(_('Error !'), _('Please config FOS Server in company.'))

            matitem_sql = """
                select
                  so.name as contractno,
                  so.client_order_ref as bookingno,
                  pp.id as itemno,
                  1 as lineseq,
                  'other' as itemtype,
                  pp.name_template as itemdesc1,
                  (select count(*) from sale_branch_line where sale_id = so.id) as storeqty,
                  product_uom_qty as totqty,
                  pu.name as qtyuom
                from 
                  sale_order so 
                join sale_order_line sol on so.id = sol.order_id
                left join omg_sale_reserve_contact osrc on so.client_order_ref = osrc.name
                left join product_product pp on sol.product_id = pp.id
                left join product_template pt on pp.product_tmpl_id = pt.id
                left join product_uom pu on pt.uom_id = pu.id
               where so.company_id = %s and so.id = %s
            """
            cr.execute(matitem_sql % (order.company_id.id, order.id))
            line_data =  cr.dictfetchall()
            for data in line_data:
                insert_field = self._genfield(data,1);
                insert_value = self._genfield(data,2);
                insert_contrmf_sql = 'insert into contr_matitem '+insert_field+' values '+insert_value
                update_contrmf_sql = "update contr_matitem set "+self._genfield(data,3)+" where contractno = '%s' and itemno = %s " % (data['contractno'],data['itemno'])
                if order.company_id.fos_host and order.company_id.fos_user and order.company_id.fos_dbname:
                    server_ip = order.company_id.fos_host
                    server_user = order.company_id.fos_user
                    server_password = order.company_id.fos_password
                    server_db = order.company_id.fos_dbname

                    conn = pymssql.connect(host=server_ip, user=server_user, password=server_password, 
                                           database=server_db,as_dict=True )
                    cur = conn.cursor()
                    try:
                        #insert_sql
                        cur.execute('SET ANSI_WARNINGS off')
                        cur.execute(insert_contrmf_sql.encode('cp874'))

                    except:
                        #update_sql
                        cur.execute('SET ANSI_WARNINGS off')
                        cur.execute(update_contrmf_sql.encode('cp874'))

                    cur.close()
                    conn.commit()
                    
                else:
                    raise osv.except_osv(_('Error !'), _('Please config FOS Server in company.'))

            asset_sql = """
                select
                  so.name as contractno,
                  so.client_order_ref as bookingno,
                  pp.id as assetcd,
                  pp.name_template as assetname,
                  (select count(*) from sale_branch_line where sale_id = so.id) * product_uom_qty as qtyneed,
                  (select count(*) from sale_branch_line where sale_id = so.id) as storeqty,
                  product_uom_qty as qtyneed,
                  pu.name as uofm
                from 
                  sale_order so 
                join sale_order_line sol on so.id = sol.order_id
                left join omg_sale_reserve_contact osrc on so.client_order_ref = osrc.name
                left join product_product pp on sol.product_id = pp.id
                left join product_template pt on pp.product_tmpl_id = pt.id
                left join product_uom pu on pt.uom_id = pu.id
               where so.company_id = %s and so.id = %s and pp.equipment = True
            """
            cr.execute(asset_sql % (order.company_id.id, order.id))
            line_data =  cr.dictfetchall()
            for data in line_data:
                insert_field = self._genfield(data,1);
                insert_value = self._genfield(data,2);
                insert_contrmf_sql = 'insert into contr_asset '+insert_field+' values '+insert_value
                update_contrmf_sql = "update contr_asset set "+self._genfield(data,3)+" where contractno = '%s' and assetcd = %s " % (data['contractno'],data['assetcd'])
                if order.company_id.fos_host and order.company_id.fos_user and order.company_id.fos_dbname:
                    server_ip = order.company_id.fos_host
                    server_user = order.company_id.fos_user
                    server_password = order.company_id.fos_password
                    server_db = order.company_id.fos_dbname

                    conn = pymssql.connect(host=server_ip, user=server_user, password=server_password, 
                                           database=server_db,as_dict=True )
                    cur = conn.cursor()
                    try:
                        #insert_sql
                        cur.execute('SET ANSI_WARNINGS off')
                        cur.execute(insert_contrmf_sql.encode('cp874') )

                    except:
                        #update_sql
                        cur.execute('SET ANSI_WARNINGS off')
                        cur.execute(update_contrmf_sql.encode('cp874'))

                    cur.close()
                    conn.commit()
                    
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
                        if isinstance(data[key], (str,unicode)) :
                            result = result+"'%s'," % data[key]
                        else:
                            result = result+"'%s'," % data[key]
                    else:
                        result = result+"%s," % data[key]
            elif (sqltype == 3):
                if data[key] == False:
                    result = result+key+"=null, "
                else: 
                    if isinstance(data[key], (str,unicode,date,datetime)):
                        if isinstance(data[key], (str,unicode)):
                            result = result+key+"='%s', " % data[key]
                        else:
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