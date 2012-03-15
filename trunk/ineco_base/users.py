# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2011 OpenERP s.a. (<http://openerp.com>).
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

from osv import fields,osv
from osv.orm import browse_record
import tools
from functools import partial
import pytz
import pooler
from tools.translate import _
from service import security
import netsvc

class users(osv.osv):
    
    _name = "res.users"
    _inherit = "res.users"
    _description = "Change Default Company ID" 
    
    def on_change_company_id(self, cr, uid, ids, company_id):
        cr.execute('UPDATE res_users SET company_id = %s WHERE id = %s ', (company_id, uid) )
        return True
    
users()