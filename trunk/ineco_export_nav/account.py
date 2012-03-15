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
# 26-12-2011       POP-001    Add NAV Payment Term

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

import pymssql

class ineco_nav_payment_term(osv.osv):
    _name = 'ineco.nav.payment.term'
    _description = 'nav payment term'
    _columns = {
        'name': fields.char('Code', size=50),
        'description': fields.char('Description', size=50),
        'company_id': fields.many2one('res.company', 'Company')
    }
    
    def schedule_sync(self, cr, uid, context=None):
        table_name = 'Payment Terms'
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
                    nav_code = row['Code']
                    nav_ids = self.pool.get('ineco.nav.payment.term').search(cr, uid , [('name','=',row['Code'])])
                    if not nav_ids:
                        data = {
                            'name':row['Code'].decode('cp874'),
                            'description': row['Description'].decode('cp874'),
                            'company_id': company.id
                        }
                        self.pool.get('ineco.nav.payment.term').create(cr, uid, data)
                    row = cur.fetchone()
                    
                cur.close()
        
ineco_nav_payment_term()

class account_payment_term(osv.osv):
    _name = "account.payment.term"
    _inherit = "account.payment.term"
    _description = "Add Code for Payment Term" 
    
    _columns = {
        'code_nav': fields.char('NAV Code', size=32, required=True),
        'nav_id': fields.many2one('ineco.nav.payment.term', 'Nav ID'),
    }
    
account_payment_term()

