# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 INECO LTD, PART. (www.ineco.co.th).
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

# 22-02-2012    POP-001    Add customer product for criteria

import time
from lxml import etree

from osv import fields, osv
from tools.translate import _

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class wizard_ineco_change_delivery_date(osv.osv_memory):

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
        datas['model'] = 'wizard.ineco.change.delivery.date'
        datas['form'] = self.read(cr, uid, ids, context=context)[0]
        
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if datas['form']['date_delivery'] and datas['form']['date_arrival'] and datas['form']['path'] and datas['form']['period_id']:
            delivery_date = datas['form']['date_delivery'] 
            arrival_date = datas['form']['date_arrival']
            path = datas['form']['path']
            period_id = datas['form']['period_id']
            sql_command = """
                update stock_picking
                set ineco_delivery_date = '%s', date_arrival = '%s'
                where type = 'out' and period_id in %s and path like '%s'            
            """ %  (delivery_date, arrival_date,tuple(period_id),path+'%')
            sql_command = sql_command.replace(',)',')')
            cr.execute(sql_command)
                        
        return self.write(cr, uid, ids, {'state':'choose','path':False }, context=context)

    _name = "wizard.ineco.change.delivery.date"
    _description = "Change Delivery Date"

    _columns = {
        'date_delivery': fields.date('Delivery Date', required=True),
        'date_arrival': fields.date('Arrival Date', required=True),
        'path': fields.char('Path', size=20, required=True),
        'period_id': fields.many2many('omg.sale.period', 'report_category_rel', 'report_id', 'period_id', 'Periods', required=True),
        'state': fields.selection( ( ('choose','choose'), ('get','get'), ) ),
    }
    
    _defaults = { 
        'state': lambda *a: 'choose',
    }    


wizard_ineco_change_delivery_date()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
