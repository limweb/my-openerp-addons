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

class wizard_report_incomming(osv.osv_memory):

    def act_cancel(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }

    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }

    def create_report(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.report.incomming'
        datas['form'] = self.read(cr, uid, ids, context=context)[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        criteries = None
        report= None
        if datas['ids']:
            criteries = 'stock_picking.id in '+ str(tuple( sorted(datas['ids'])))
            criteries = criteries.replace(',)',')')
            
        if criteries:
            host_ids = self.pool.get('omg.configuration').search(cr, uid, [('type','=','jasper')])
            hostname = 'localhost'
            if host_ids:
                host_obj = self.pool.get('omg.configuration').browse(cr, uid, host_ids)[0]
                hostname = host_obj['host']
                
            url = 'http://'+hostname+':8000/jasperserver/services/repository?wsdl'
            j = jasperclient.JasperClient(url,host_obj.username,host_obj.password)
            a = j.runReport('/Openerp/OA/omg-incomming-order',this.format, {'pick_ids': criteries})
            this.name = "%s.%s" % ('incomming', this.format)
            buf = StringIO()
            buf.write(a['data'])
            report = base64.encodestring(buf.getvalue())
            buf.close()
        return self.write(cr, uid, ids, {'state':'get', 'report':report, 'name':this.name}, context=context)

    _name = "wizard.report.incomming"
    _description = "New Incomming Report Style"

    _columns = {
        'name': fields.char('Filename', 16, readonly=True),                
        'report': fields.binary('Report File'),
        'state': fields.selection( ( ('choose','choose'), ('get','get'), ) ),
        'format': fields.selection( ( ('csv','CSV File'), ('pdf','PDF File'), ('xls', 'Excel 2003')), 'File Format', required=True),        
    }
    _defaults = { 
        'state': lambda *a: 'choose',
        'name': lambda *a: 'incomming.pdf'
    }    


wizard_report_incomming()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
