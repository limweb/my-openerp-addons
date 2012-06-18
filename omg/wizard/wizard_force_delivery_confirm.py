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
#18-06-2012        POP-001        Create New Report

import time
from lxml import etree

from osv import fields, osv
from tools.translate import _
import jasperclient
import base64
import csv
import codecs

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class wizard_ineco_force_delivery_confirm(osv.osv_memory):

    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }

    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }

    def force_confirm(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.ineco.delivery.forceconfirm'
        datas['form'] = self.read(cr, uid, ids, context=context)[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        user_obj = self.pool.get('res.users').browse(cr, uid, uid)
        if datas['ids'] and datas['form']['check_sure'] :
            delivery_ids = datas['ids']
            if len(datas['ids']) == 1:
                value = str(tuple(delivery_ids)).replace(',','')
            else:
                value = str(tuple(delivery_ids))
            sql_stock_move = """
                update stock_move
                set state = 'done', location_id = 8
                where picking_id in (select id from stock_picking
                  where picking_id in %s and type = 'out')
                  and state <> 'cancel'
            """
            cr.execute(sql_stock_move % value )
            sql_stock_picking = """
                update stock_picking
                set state = 'done'
                where state <> 'cancel' and type = 'out' and id in %s         
            """
            cr.execute(sql_stock_picking % value)
            return {'type':'ir.actions.act_window_close' }
        else:          
            return {'type':'ir.actions.act_window_close' }
    
    _name = "wizard.ineco.delivery.forceconfirm"
    _description = "Force Delivery Confirm"

    _columns = {
        'name': fields.char('Filename', 16, readonly=True),       
        'check_sure': fields.boolean('Force Confirmation'),
        'state': fields.selection( ( ('choose','choose'), ('get','get'), ) ),
    }
    _defaults = { 
        'check_sure': 0,
        'state': 'choose',
    }    

wizard_ineco_force_delivery_confirm()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
