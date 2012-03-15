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

class ineco_logistic_path(osv.osv):
    
    _name = "ineco.logistic.path"
    _description = "Ineco Logistic Path"

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if context is None:
            context = {}
        if not len(ids):
            return []
        reads = self.read(cr, uid, ids, ['name','path_id'], context=context)
        for record in reads:
            name = record['name']
            if context.get('full',False):
                if record['path_id']:
                    name = record['path_id'][1] + ' / ' + name
                res.append((record['id'], name))
            else:
                res.append((record['id'], name))
        return res

    def _complete_name(self, cr, uid, ids, name, args, context=None):
        """ Forms complete name of location from parent location to child location.
        @return: Dictionary of values
        """
        def _get_one_full_name(location, level=4):
            if location.path_id:
                parent_path = _get_one_full_name(location.path_id, level-1) + "->"
            else:
                parent_path = ''
            return parent_path + location.name
        res = {}
        for m in self.browse(cr, uid, ids, context=context):
            res[m.id] = _get_one_full_name(m)
        return res

    _columns = {
        'name': fields.char('Path', size=30),
        'path_id': fields.many2one('ineco.logistic.path', 'Parent'),        
        'complete_name': fields.function(_complete_name, method=True, type='char', size=120, string="Full Path"),
        'type': fields.selection([('view', 'View'), ('transport', 'Transport')], 'Type', required=True),    
        'delivery_day': fields.selection([('0','Monday'),('1','Tuesday'),('2','Wednesday'),('3','Thursday'),('4','Friday'),('5','Saturday'),('6','Sunday')], 'Delivery Day'),
        'arrival_day': fields.selection([('0','Monday'),('1','Tuesday'),('2','Wednesday'),('3','Thursday'),('4','Friday'),('5','Saturday'),('6','Sunday')], 'Arrival Day'),
    }
    
ineco_logistic_path()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

