# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from datetime import datetime
from osv import osv, fields
from tools.translate import _
import netsvc
import time
import tools
import decimal_precision as dp

class res_partner(osv.osv):
    
    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Add Fos Code In Product.Product'
    _columns = {
        'ineco_fos_code': fields.char('FOS Code', size=20),
    }
    
res_partner()