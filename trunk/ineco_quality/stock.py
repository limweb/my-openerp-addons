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

class stock_move(osv.osv):
    _name = "stock.move"
    _inherit = "stock.move" 
    _description = "Add Quality Control/Assurance"
    _columns = {
        'ineco_quality_hold': fields.boolean('Hold'),
        'ineco_quality_pass': fields.boolean('Pass'),
    }
    _defaults = {
        'ineco_quality_hold': False,
        'ineco_quality_pass': False,
    }
    
    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms stock move.
        @return: List of ids.
        """
        moves = self.browse(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'confirmed'})
        for move in moves:
            if move.product_id.ineco_quality and not move.ineco_quality_pass:
                 self.write(cr, uid, move.id, {'ineco_quality_hold': True, 'state':'waiting'})
        self.create_chained_picking(cr, uid, moves, context)
        return []
    
    def force_assign(self, cr, uid, ids, context=None):
        """ Changes the state to assigned.
        @return: True
        """
        moves = self.browse(cr, uid, ids, context=context)
        for move in moves:
            if not move.ineco_quality_hold or move.ineco_quality_pass:
                self.write(cr, uid, move.id, {'state': 'assigned'})
        return True
    
    def action_qcpass(self, cr, uid, ids, context=None):
        moves = self.browse(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'ineco_quality_pass': True, 'state': 'done'})        
        return True
    
    
stock_move()