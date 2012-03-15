# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 INECO LTD, PARTNERSHIP (<http://www.ineco.co.th>).
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

#DATE             ID         DESCRIPTION
#01-01-2012       POP-001    Create New

import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp
import netsvc

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from operator import itemgetter
from itertools import groupby


class stock_picking(osv.osv):
    
    def _get_volume(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.move_lines :
                volume = 0
                for move in line.move_lines:
                    volume = volume + (move.product_id.volume * move.product_qty or 0.0)
                res[line.id] = volume
        return res

    def _get_weight(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.move_lines :
                value = 0
                for move in line.move_lines:
                    value = value + (move.product_id.weight * move.product_qty or 0.0)
                res[line.id] = value
        return res
    
    _name = "stock.picking"
    _description = "Ineco Stock Picking"
    _inherit = "stock.picking"
    _columns = {
        'ineco_logistic_path': fields.many2one('ineco.logistic.path', 'Logistic Path'),
        'ineco_total_volume': fields.function(_get_volume, method=True, type='float', string='Gross Volume (m3)'),
        'ineco_total_weight': fields.function(_get_weight, method=True, type='float', string='Gross Weight (KGs)'),
    }

stock_picking()

class stock_location(osv.osv):
    _name = "stock.location"
    _inherit = "stock.location"
    _description = "Ineco Logistic Stock Location" 
    _columns = {
        'ineco_logistic_path': fields.many2one('ineco.logistic.path', 'Logistic Path'),
    }
stock_location()