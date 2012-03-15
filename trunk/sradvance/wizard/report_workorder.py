# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time
from lxml import etree

from osv import fields, osv
from tools.translate import _
import jasperclient
import base64

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class wizard_ineco_workorder_report(osv.osv_memory):

    def act_cancel(self, cr, uid, ids, context=None):
        #self.unlink(cr, uid, ids, context)
        return {'type':'ir.actions.act_window_close' }

    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }

    def create_report(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.ineco.workorder.report'
        datas['form'] = self.read(cr, uid, ids, context=context)[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        #customer_product = self.pool.get('product.product').browse(cr, uid, [datas['form']['product_id']])[0] or False
        production_date = datas['form']['date']
            
        hostname = '10.10.10.250'
            
        url = 'http://'+hostname+':8000/jasperserver/services/repository?wsdl'
        j = jasperclient.JasperClient(url,'jasperadmin','jasperadmin')
        a = j.runReport('/openerp/sradvance/workorder',this.format,\
            {'param_production_date': production_date })
        this.name = "%s.%s" % ('status', this.format)
        buf = StringIO()
        buf.write(a['data'])
        report = base64.encodestring(buf.getvalue())
        buf.close()
        return self.write(cr, uid, ids, {'state':'get', 'report':report, 'name':this.name}, context=context)
        #return self.write(cr, uid, ids, {'report':report}, context=context)

    _name = "wizard.ineco.workorder.report"
    _description = "Workorder Report"

    _columns = {
        'name': fields.char('Filename', 16, readonly=True),
        'date': fields.date('Production Date'),           
        'report': fields.binary('Report File'),             
        'state': fields.selection( ( ('choose','choose'), ('get','get'), ) ),
        'format': fields.selection( ( ('csv','CSV File'), ('pdf','PDF File'), ('xls', 'Excel 2003')), 'File Format', required=True),        
    }
    _defaults = { 
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'choose',
        'name': lambda *a: 'workorder.pdf',
        'format':  lambda *a: 'pdf'
    }    


wizard_ineco_workorder_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
