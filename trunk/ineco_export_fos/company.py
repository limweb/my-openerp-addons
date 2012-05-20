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

from operator import itemgetter

class res_company(osv.osv):
    _name = 'res.company'
    _inherit = 'res.company'
    _columns = {
        'fos_host': fields.char('Server IP', size=50),
        'fos_user': fields.char('User Name', size=50),
        'fos_password': fields.char('Password', size=50),
        'fos_dbname': fields.char('Database Name', size=50)
    }
res_company()