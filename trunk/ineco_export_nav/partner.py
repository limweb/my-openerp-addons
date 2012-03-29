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
import pymssql

from operator import itemgetter

class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Export Partner Class'
    _columns = {
        'supplier_posting_group_id': fields.many2one('ineco.nav.postmaster','Vendor Posting Group'),
        'customer_posting_group_id': fields.many2one('ineco.nav.postmaster','Customer Posting Group'),
        'gen_bus_posting_group_id': fields.many2one('ineco.nav.postmaster', 'Gen. Bus. Posting Group'),
        'vat_bus_posting_group_id': fields.many2one('ineco.nav.postmaster', 'VAT. Bus. Posting Group'),
        'wht_bus_posting_group_id': fields.many2one('ineco.nav.postmaster','WHT. Bus. Posting Group'),
    }
    
    def schedule_update_supplier_nav(self, cr, uid, context=None):
        table_name = 'Vendor'
        field_key = 'No_'
        field_lastupdate = 'Last Interfaced'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] where len(ltrim([Open ERP No_])) > 0 and left([Open ERP No_],1) <> 'V'
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    #print "No=%s, Name=%s" % (row['No_'], row['Name'].decode('cp874'))
                    #todo update 
                    if row['Open ERP No_'] and row['Open ERP No_'][0:1] <> 'V':
                        partner_ids = self.pool.get('res.partner').search(cr, uid, [('id','=',row['Open ERP No_'])] )
                        if partner_ids:
                            partner = self.pool.get('res.partner').browse(cr, uid, partner_ids)[0]
                            partner.write({'ref': row['No_']})  
                    row = cur.fetchone()
                    
                cur.close()
        return True

    def schedule_update_customer_nav(self, cr, uid, context=None):
        table_name = 'Customer'
        field_key = 'No_'
        field_lastupdate = 'Last Interfaced'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] where len(ltrim([Open ERP No_])) > 0 and left([Open ERP No_],1) <> 'C'
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    #print "No=%s, Name=%s" % (row['No_'], row['Name'].decode('cp874'))
                    #todo update 
                    if row['Open ERP No_'] and row['Open ERP No_'][0:1] <> 'C':
                        partner_ids = self.pool.get('res.partner').search(cr, uid, [('id','=',row['Open ERP No_'])] )
                        if partner_ids:
                            partner = self.pool.get('res.partner').browse(cr, uid, partner_ids)[0]
                            partner.write({'ref': row['No_']})  
                    row = cur.fetchone()
                    
                cur.close()
        return True
    
    def schedule_export_new(self, cr, uid, context=None):
        if context is None:
            context = {}
        sql = """
            select id from res_partner
            where write_uid is null and ineco_sync_id is not null
        """
        #only new partner record... Please install ineco_inter_company
        cr.execute(sql)
        new_ids = map(itemgetter(0), cr.fetchall())
        for row in new_ids:
            self.export_nav(cr, uid, [row], context)
            self.write(cr, uid, [row], {'date': time.strftime('%Y-%m-%d %H:%M:%S') })
        return True

    def export_nav(self, cr, uid, ids, context={}):
        for partner in self.pool.get('res.partner').browse(cr, uid, ids):
            addr = self.pool.get('res.partner').address_get(cr, uid, [partner.id], ['invoice']) 
            address_invoice = False    
            if addr and addr['invoice']:
                address_invoice = self.pool.get('res.partner.address').browse(cr, uid, addr['invoice'])
            else:
                err_message = 'Please insert Invoice Address in Partner master:' + partner.name
                self.log(cr, uid, partner.id, err_message)
                raise osv.except_osv(_('Error !'), err_message)
                
            config_ids = self.pool.get('ineco.export.config').search(cr, uid, [('type','=','supplier'),('company_id','=',partner.company_id.id)])
            config_obj = self.pool.get('ineco.export.config').browse(cr, uid, config_ids)
            if config_obj and addr:
                config_ids = self.pool.get('ineco.export.config').search(cr, uid, [('type','=','supplier'),('company_id','=',partner.company_id.id)])
                config_obj = self.pool.get('ineco.export.config').browse(cr, uid, config_ids)
                config = config_obj[0]
                path = False
                if partner.supplier:
                    path = config.path+"VEND"+('%.4d' % partner.id)+"-"+str(partner.company_id.id)+".csv"   
                    #path = config.path+"supplier-"+str(partner.company_id.id)+"-"+str(partner.id)+".csv"
                    #POP-001
                    f = open(path, 'wt')
                    #f = codecs.open(path, encoding='cp874', mode='w+')
                    #writer = csv.writer(f)
                    writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                    code = False
                    if partner.ref:
                        code = partner.ref
                    else:
                        code = partner.id
                    writer.writerow([code ,  
                                     partner.name[0:50].encode('cp874'), 
                                     partner.name[50:0].encode('cp874'), 
                                     address_invoice.street.encode('cp874') or "", 
                                     address_invoice.street2.encode('cp874') or "",
                                     "",
                                     address_invoice.city.encode('cp874') or "", #NAV Master
                                     address_invoice.state_id.name.encode('cp874') or "", #NAV Master
                                     address_invoice.zip or "", #NAV Master
                                     address_invoice.country_id.code or "", #NAV Master
                                     address_invoice.name.encode('cp874') or "",
                                     address_invoice.phone or "",
                                     address_invoice.fax or "",
                                     partner.supplier_posting_group_id.code_nav or "",
                                     partner.gen_bus_posting_group_id.code_nav or "",
                                     partner.vat_bus_posting_group_id.code_nav or "",
                                     partner.wht_bus_posting_group_id.code_nav or "",
                                     partner.property_payment_term.code_nav or "",
                                     "", #Block 'All'
                                     partner.tax_id or "",
                                     time.strftime('%d/%m/%Y %H:%M')
                                     ])

            if partner.customer:
                config_ids = self.pool.get('ineco.export.config').search(cr, uid, [('type','=','customer'),('company_id','=',partner.company_id.id)])
                config_obj = self.pool.get('ineco.export.config').browse(cr, uid, config_ids)
                if config_obj and addr:
                    config = config_obj[0]
                    path = config.path+"CUST"+('%.4d' % partner.id)+"-"+str(partner.company_id.id)+".csv"
                    #POP-001   
                    f = open(path, 'wt')
                    #f = codecs.open(path, encoding='cp874', mode='w+')
                    #writer = csv.writer(f)
                    writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                    code = False
                    if partner.ref:
                        code = partner.ref
                    else:
                        code = partner.id
                    writer.writerow([code , 
                                     partner.name[0:50].encode('cp874'), 
                                     partner.name[50:0].encode('cp874'), 
                                     address_invoice.street.encode('cp874') or "", 
                                     address_invoice.street2.encode('cp874') or "",
                                     "",
                                     address_invoice.city.encode('cp874') or "", #NAV Master
                                     address_invoice.state_id.name.encode('cp874') or "", #NAV Master
                                     address_invoice.zip or "", #NAV Master
                                     address_invoice.country_id.code or "", #NAV Master
                                     address_invoice.name.encode('cp874') or "",
                                     address_invoice.phone or "",
                                     address_invoice.fax or "",
                                     partner.customer_posting_group_id.code_nav or "",
                                     partner.gen_bus_posting_group_id.code_nav or "",
                                     partner.vat_bus_posting_group_id.code_nav or "",
                                     partner.wht_bus_posting_group_id.code_nav or "",
                                     partner.property_payment_term.code_nav or "",
                                     "", #Block "All"
                                     partner.tax_id or "",
                                     time.strftime('%d/%m/%Y %H:%M'),
                                     partner.credit_limit or 0 ])
        return True

    def write(self, cr, uid, ids, vals, context=None):
        update_id = super(res_partner, self).write(cr, uid, ids, vals, context=context)
        if context is None:
            context = {}
        obj = self.read(cr, uid, ids)[0]
        sync_id = obj['ineco_sync_id']
        res_ids = ids
        if sync_id:
            res_ids = self.pool.get('res.partner').search(cr, uid, [('ineco_sync_id','=',sync_id)])
            self.export_nav(cr, uid, res_ids, context)
        return  update_id
    
res_partner()