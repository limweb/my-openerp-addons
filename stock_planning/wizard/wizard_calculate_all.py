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

#
#02-06-2012        POP-001        Create New Report

import time
from lxml import etree

from osv import fields, osv
from tools.translate import _

import base64
import csv
import codecs

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class wizard_ineco_calculate_all(osv.osv_memory):

    def act_cancel(self, cr, uid, ids, context=None):
        #self.unlink(cr, uid, ids, context)
        return {'type':'ir.actions.act_window_close' }

    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }

    def execute(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.ineco.calculate.all'
        datas['form'] = self.read(cr, uid, ids, context=context)[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        user_obj = self.pool.get('res.users').browse(cr, uid, uid)
        if datas['ids']:
            planning = self.pool.get('stock.planning')
            for plan in  self.pool.get('stock.planning').browse(cr, uid, ids):
                planning.calculate_planning(cr, uid, datas['ids'], context)
        return {'type':'ir.actions.act_window_close' }
    
    _name = "wizard.ineco.calculate.all"
    _description = "Calculate All"

    _columns = {
        'name': fields.char('Filename', 16, readonly=True),       
        'state': fields.selection( ( ('choose','choose'), ('get','get'), ) ),
    }
    _defaults = { 
        'state': lambda *a: 'choose',
        'name': lambda *a: 'adjust_report.pdf',
    }    

wizard_ineco_calculate_all()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
