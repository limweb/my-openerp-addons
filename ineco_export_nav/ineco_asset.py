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

from datetime import datetime
from operator import itemgetter

import pymssql

class ineco_nav_fa_posting_group(osv.osv):
    _name = 'ineco.nav.fa.posting.group'
    _description = 'nav fa posting group'
    _columns = {
        'name': fields.char('Code', size=50),
        'description': fields.char('Description', size=50),
        'company_id': fields.many2one('res.company', 'Company')
    }
    
    def schedule_sync(self, cr, uid, context=None):
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
                    nav_ids = self.pool.get('ineco.nav.fa.posting.group').search(cr, uid , [('name','=',row['Code'])])
                    if not nav_ids:
                        data = {
                            'name':row['Code'].decode('cp874'),
                            'description': row['Code'].decode('cp874'),
                            'company_id': company.id
                        }
                        self.pool.get('ineco.nav.fa.posting.group').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()
        
ineco_nav_fa_posting_group()

class ineco_asset(osv.osv):
    
    _name = "ineco.asset"
    _description = "Export Asset"
    _inherit = "ineco.asset" 
    
    _columns = {
        'nav_exported': fields.boolean('Exported'),
        'fa_posting_group_id': fields.many2one('ineco.nav.postmaster', 'FA Posting Group'),
        'nav_id': fields.many2one('ineco.nav.fa.posting.group', 'Nav ID')
    }
    
    _defaults = {
        'nav_exported': False,
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        vals.update({'nav_exported': False})
        return super(ineco_asset, self).write(cr, uid, ids, vals, context=context)

    def schedule_export_asset_nav(self, cr, uid, context=None):
        if context is None:
            context = {}
        user_obj = self.pool.get('res.users').browse(cr, uid, [uid])[0]
        asset_ids = self.pool.get('ineco.asset').search(cr, uid, [('nav_exported','=',False)])
        for asset in self.pool.get('ineco.asset').browse(cr, uid, asset_ids):
            config_ids = self.pool.get('ineco.export.config').search(cr, uid, [('type','=','asset'),('company_id','=',asset.company_id.id)])
            config_obj = self.pool.get('ineco.export.config').browse(cr, uid, config_ids)   
            if config_obj:   
                config = config_obj[0]
                path = config.path+"FA"+('%.4d' % asset.id)+".csv"   
#                path = config.path+"asset-"+str(asset.company_id.id) +"-"+str(asset.id)+".csv"
                #POP-001
                #f = open(path, 'wt')
                f = codecs.open(path, encoding='cp874', mode='w+')
                writer = csv.writer(f)
                writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
                writer.writerow([
                    asset.name, 
                    asset.product_id.name[:30] or "",
                    asset.product_id.name[30:] or "",
                    asset.asset_type_id.code_nav or "", #FA Class Code -> ERP.ineco_asset_type
                    'COM', # asset.location_id and asset.location_id.code or "", #FA Location Code -> ERP.location_id
                    '0001' , #asset.owner_id and asset.owner_id.code_nav or "", #FA Responsible Employee -> ERP.owner_id
                    asset.name or "", #Barcode No
                    "", #Yes, No
                    asset.fa_posting_group_id.code_nav or "", #FA Post Group
                    "Company",
                    "Straight-Line",
                    datetime.strptime(asset.register_date, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y'), #Start Date
                    asset.percent,
                    time.strftime('%d/%m/%Y %H:%M'),
                ])
                cr.execute("update ineco_asset set nav_exported = True where id = %s " % asset.id)
        return True
    
ineco_asset()

class ineco_asset_type(osv.osv):
    _name = "ineco.asset.type"
    _inherit = "ineco.asset.type"
    _description = "Export NAV Class Code" 
    _columns = {
        'code_nav': fields.char('NAV Code', size=32),
    }
ineco_asset_type()