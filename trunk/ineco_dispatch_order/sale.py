# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

# 11-10-2012    POP-001    Initial

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

class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
        'dispatch_order_id': fields.many2one('ineco.dispatch.order','Dispatch Order'),
    }
    _defaults = {
        'dispatch_order_id': False,    
    }
sale_order()
