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

import time
import netsvc

import decimal_precision as dp

from osv import fields,osv
from tools.translate import _

import os
import sys
import math
import base64

class ineco_main(osv.osv):

    _name = "ineco.main"
    _description = "Main Object"
    _order = 'name'

    _columns = {
        'name': fields.char('Data ID', size=32, select=True, required=True),
        'total': fields.integer('Total'),
        'state': fields.selection([('draft','Draft'),('open','Open'),('done1','Approve'),('done2','Manager Approval')], 'State', readonly=True),
    }

    _defaults = {
        'total': 0,
        'state': 'draft',
    }

    _sql_constraints = [
        ('name_main_uniq', 'unique (name)', 'Main code must be unique !')
    ]    

    def _check_sale_approve(self, cr, uid, ids, context=None):
        res = {}
        for data in self.browse(cr, uid, ids, context=context):
            if data.total < 100000:
                print "Sale"
                res[data.id] = True
            else:
                print "Manager"
                res[data.id] = False
        return res

    def _check_manager_approve(self, cr, uid, ids, context=None):
        res = {}
        for data in self.browse(cr, uid, ids, context=context):
            result = False
            if data.total >= 100000:
                res[data.id] = True
            else:
                res[data.id] = False
        return res

    def workflow_start(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        return []

    def workflow_open(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'open'})
        return []

    def workflow_done1(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'done1'})
        return []

    def workflow_done2(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'done2'})
        return []

ineco_main()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
