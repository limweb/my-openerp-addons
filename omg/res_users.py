# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 INECO LIMITED PARTNERSHIP (<http://www.ineco.co.th>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

# 25-04-2012    POP-001    Initial 

import socket
import sys

import time
import netsvc
import asset

import sale
import sale_period

import decimal_precision as dp

from osv import fields,osv
from tools.translate import _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

import re

import tools 

class res_users(osv.osv):
    _name = 'res.users'
    _inherit = 'res.users'
    
    _columns = {
        'read_only_product_name': fields.boolean('Read Product Name Only'),
    }
    
    _defaults = {
        'read_only_product_name': False,
    }
    
res_users()