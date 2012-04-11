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
from operator import itemgetter

import netsvc

import pymssql

class ineco_export_config(osv.osv):
    _name = "ineco.export.config"
    _description = "Configuration path to keep csv files."
    _columns = {
        'name': fields.char('Description', size=128, required=True),
        'type': fields.selection([('supplier','Supplier'),('customer','Customer'),('purchase','Purchase'),('sale','Sale'),('asset','Asset'),('pretty','Pretty Cash'),('store','Store')],string="Data Type"),
        'path': fields.char('Save Path', size=254, required=True),        
        'company_id': fields.many2one('res.company','Company', required=True, ondelete='restrict'),
    }
    
    _defaults = {
        'type': 'supplier',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }

    _sql_constraints = [
        ('type_company_unique', 'unique (type, company_id)', 'The type must be unique per company !'),
    ]

    def copy(self, cr, uid, id, default={}, context={}):
        type = self.read(cr, uid, [id], ['type'])[0]['type']
        company_sql = """
            select id from res_company
            where id not in (
            select company_id from ineco_export_config where type = '%s') 
            and parent_id is not null 
        """
        cr.execute(company_sql % type)
        company_ids = map(itemgetter(0), cr.fetchall())
        company = self.pool.get('res.company').browse(cr, uid, company_ids)
        name = self.read(cr, uid, [id], ['name'])[0]['name']
        if company:
            default.update({'name': name+ _(' (copy)'), 'company_id': company[0].id})
        return super(ineco_export_config, self).copy(cr, uid, id, default, context)
    
ineco_export_config()

class ineco_nav_dimension_group(osv.osv):
    _name = "ineco.nav.dimension.group"
    _description = "Group of Dimension"
    _columns = {
        'name': fields.char('Name of Group', size=128, required=True),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'active': True,
    }
ineco_nav_dimension_group()

class ineco_nav_dimension(osv.osv):
    _name = "ineco.nav.dimension"
    _description = "NAV Dimension"
    _columns = {
        'code': fields.char('Code', size=64, required=True),
        'name': fields.char('Name', size=128, required=True),
        'group_dimension': fields.selection([('company','COMPANY'),('department','DEPARTMENT'),('project','PROJECT'),('product','PRODUCT'),('retailer','Retailer'),('customer','CUSTOMER'),('employee','EMPLOYEE ADV'),('network','NETWORK PARTNERS')],string="Data Type"),
#        'group_dimension': fields.many2one('ineco.nav.dimension.group', 'Group', required=True, ondelete='restrict'),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('dimension_code_group_unique', 'unique (code, name, group_dimension)', 'The CODE must be unique per GROUP !'),
    ]

    def schedule_sync(self, cr, uid, context=None):
        table_name = 'Dimension Value'
        field_key = 'Code'
        field_desc = 'Name'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] 
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    try:
                        nav_ids = self.pool.get('ineco.nav.dimension').search(cr, uid , [('code','=',row['Code'].decode('cp874')),('name','=',row['Name'].decode('cp874'))])
                        group_dimension = False
                        if row['Dimension Code'] == 'EMPLOYEE ADV':
                            group_dimension = 'employee'
                        elif row['Dimension Code'] == 'NETWORK PARTNERS':
                            group_dimension = 'network'
                        else:
                            group_dimension = row['Dimension Code'].lower()
                        if not nav_ids:
                            data = {
                                'code':row['Code'].decode('cp874'),
                                'name': row['Name'].decode('cp874') or False,
                                'group_dimension': group_dimension,
                                #'company_id': company.id
                            }
                            self.pool.get('ineco.nav.dimension').create(cr, uid, data)
                    except:
                        pass
                    row = cur.fetchone()
                    
                cur.close()
    
ineco_nav_dimension()

class ineco_nav_dimension_value(osv.osv):
    _name = "ineco.nav.dimension.value"
    _description = "NAV Dimension Value"
    _columns = {
        'code': fields.char('Code', size=64, required=True),
        'name': fields.char('Name', size=128, required=True),
        'dimension_id': fields.many2one('ineco.nav.dimension', 'Dimension'), 
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'active': True,
    }

    def schedule_sync(self, cr, uid, context=None):
        table_name = 'Dimension Value'
        field_key = 'Code'
        field_desc = 'Name'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] 
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    nav_ids = self.pool.get('ineco.nav.dimension.value').search(cr, uid , [('code','=',row['Code']),('name','=',row['Name'])])
                    dimension_ids = self.pool.get('ineco.nav.dimension').search(cr, uid, [('code','=',row['Dimension Code'])])
                    if not nav_ids:
                        data = {
                            'code':row['Code'].decode('cp874'),
                            'name': row['Name'].decode('cp874'),
                            'dimension_id': dimension_ids[0] or False,
                        }
                        self.pool.get('ineco.nav.dimension.value').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()
    
ineco_nav_dimension()
    
ineco_nav_dimension_value()

class ineco_nav_postmaster_group(osv.osv):
    
    _name = "ineco.nav.postmaster.group"
    _description = "Posting Group"
    _columns = {
        'name': fields.char('Name of Posting Group', size=128, required=True),
        'code_nav': fields.char('Code', size=32),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'active': True,
    }
    
ineco_nav_postmaster_group()

class ineco_nav_postmaster(osv.osv):
    _name = "ineco.nav.postmaster"
    _description = "Master Posting Group"
    
    _columns = {
        'name': fields.char('Description', size=128, required=True),
        'code_nav': fields.char('NAV Code', size=32, required=True),
        'group_nav': fields.selection([
                    ('customer','Customer Posting Group'),
                    ('vendor','Vendor Posting Group'),
                    ('general','General Business Posting Group'),
                    ('asset','Asset Posting Group'),
                    ('vat','Vat Business Posting Group'),
                    ('wht','With Holding Tax Business Posting Group'),
                    ('genbus','Gen Business Posting Group'),
                    ('vatproduct','Vat Product Posting Group'),
                    ('whtproduct','WHT Product Posting Group'),
                    ('genproduct','Gen Product Posting Group') ],'Group'),
        'active': fields.boolean('Active'),
    }
    
    _defaults = {
        'active': True,
    }
    
    def schedule_sync_customer(self, cr, uid, context=None):
        table_name = 'Customer Posting Group'
        field_key = 'Code'
        field_desc = 'Code'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] 
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    nav_ids = self.pool.get('ineco.nav.postmaster').search(cr, uid , [('name','=',row['Code'])])
                    if not nav_ids:
                        data = {
                            'name':row['Code'].decode('cp874'),
                            'code_nav': row['Code'].decode('cp874'),
                            'group_nav': 'customer'
                        }
                        self.pool.get('ineco.nav.postmaster').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()

    def schedule_sync_vendor(self, cr, uid, context=None):
        table_name = 'Vendor Posting Group'
        field_key = 'Code'
        field_desc = 'Code'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] 
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    nav_ids = self.pool.get('ineco.nav.postmaster').search(cr, uid , [('name','=',row['Code'])])
                    if not nav_ids:
                        data = {
                            'name':row['Code'].decode('cp874'),
                            'code_nav': row['Code'].decode('cp874'),
                            'group_nav': 'vendor'
                        }
                        self.pool.get('ineco.nav.postmaster').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()

    def schedule_sync_gen(self, cr, uid, context=None):
        table_name = 'Gen_ Business Posting Group'
        field_key = 'Code'
        field_desc = 'Code'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] 
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    nav_ids = self.pool.get('ineco.nav.postmaster').search(cr, uid , [('name','=',row['Code'])])
                    if not nav_ids:
                        data = {
                            'name':row['Code'].decode('cp874'),
                            'code_nav': row['Code'].decode('cp874'),
                            'group_nav': 'general'
                        }
                        self.pool.get('ineco.nav.postmaster').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()
 
    def schedule_sync_asset(self, cr, uid, context=None):
        table_name = 'FA Posting Group'
        field_key = 'Code'
        field_desc = 'Description'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] 
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    nav_ids = self.pool.get('ineco.nav.postmaster').search(cr, uid , [('name','=',row['Code'])])
                    if not nav_ids:
                        data = {
                            'name':row['Code'].decode('cp874'),
                            'code_nav': row['Code'].decode('cp874'),
                            'group_nav': 'asset'
                        }
                        self.pool.get('ineco.nav.postmaster').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()

    def schedule_sync_vat(self, cr, uid, context=None):
        table_name = 'VAT Business Posting Group'
        field_key = 'Code'
        field_desc = 'Code'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] 
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    nav_ids = self.pool.get('ineco.nav.postmaster').search(cr, uid , [('name','=',row['Code'])])
                    if not nav_ids:
                        data = {
                            'name':row['Code'].decode('cp874'),
                            'code_nav': row['Code'].decode('cp874'),
                            'group_nav': 'vat'
                        }
                        self.pool.get('ineco.nav.postmaster').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()

    def schedule_sync_wht(self, cr, uid, context=None):
        table_name = 'WHT Business Posting Group'
        field_key = 'Code'
        field_desc = 'Code'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] 
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    nav_ids = self.pool.get('ineco.nav.postmaster').search(cr, uid , [('name','=',row['Code'])])
                    if not nav_ids:
                        data = {
                            'name':row['Code'].decode('cp874'),
                            'code_nav': row['Code'].decode('cp874'),
                            'group_nav': 'wht'
                        }
                        self.pool.get('ineco.nav.postmaster').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()

    def schedule_sync_genbus(self, cr, uid, context=None):
        table_name = 'Gen_ Business Posting Group'
        field_key = 'Code'
        field_desc = 'Code'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] 
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    nav_ids = self.pool.get('ineco.nav.postmaster').search(cr, uid , [('name','=',row['Code']+' (gen)')])
                    if not nav_ids:
                        data = {
                            'name':row['Code'].decode('cp874')+' (gen)',
                            'code_nav': row['Code'].decode('cp874')+' (gen)',
                            'group_nav': 'genbus'
                        }
                        self.pool.get('ineco.nav.postmaster').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()

    def schedule_sync_vatproduct(self, cr, uid, context=None):
        table_name = 'VAT Product Posting Group'
        field_key = 'Code'
        field_desc = 'Code'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] 
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    nav_ids = self.pool.get('ineco.nav.postmaster').search(cr, uid , [('name','=',row['Code'])])
                    if not nav_ids:
                        data = {
                            'name':row['Code'].decode('cp874'),
                            'code_nav': row['Code'].decode('cp874'),
                            'group_nav': 'vatproduct'
                        }
                        self.pool.get('ineco.nav.postmaster').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()

    def schedule_sync_whtproduct(self, cr, uid, context=None):
        table_name = 'WHT Product Posting Group'
        field_key = 'Code'
        field_desc = 'Code'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] 
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    nav_ids = self.pool.get('ineco.nav.postmaster').search(cr, uid , [('name','=',row['Code'])])
                    if not nav_ids:
                        data = {
                            'name':row['Code'].decode('cp874'),
                            'code_nav': row['Code'].decode('cp874'),
                            'group_nav': 'whtproduct'
                        }
                        self.pool.get('ineco.nav.postmaster').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()

    def schedule_sync_genproduct(self, cr, uid, context=None):
        table_name = 'Gen_ Product Posting Group'
        field_key = 'Code'
        field_desc = 'Code'
        company_ids = self.pool.get('res.company').search(cr, uid, [])
        for company in self.pool.get('res.company').browse(cr, uid, company_ids ):
            if company.ineco_nav_table and company.nav_dbname and company.nav_user and company.nav_password and company.nav_host:
                sql = """
                    select * from [%s%s] 
                """
                conn = pymssql.connect(host=company.nav_host, user=company.nav_user, password=company.nav_password, database=company.nav_dbname,as_dict=True)
                cur = conn.cursor()
                sql_complete = sql % (company.ineco_nav_table,table_name) 
                cur.execute(sql_complete )
                row = cur.fetchone()
                while row:
                    nav_ids = self.pool.get('ineco.nav.postmaster').search(cr, uid , [('name','=',row['Code'])])
                    if not nav_ids:
                        data = {
                            'name':row['Code'].decode('cp874'),
                            'code_nav': row['Code'].decode('cp874'),
                            'group_nav': 'genproduct'
                        }
                        self.pool.get('ineco.nav.postmaster').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()
    
ineco_nav_postmaster()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: