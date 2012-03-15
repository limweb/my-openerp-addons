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
#12-02-2012        POP-001        Create New Report

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

class wizard_report_pivot_summary_delivery_by_period(osv.osv_memory):

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
        datas['model'] = 'wizard.ineco.report.pivot.delivery.period.summary'
        datas['form'] = self.read(cr, uid, ids, context=context)[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        period_id = datas['form']['period_id']
        report_name = datas['form']['name']

        host_ids = self.pool.get('ineco.report.config').search(cr, uid, [('type','=','report.pivot.delivery.period.summary')])
        hostname = 'localhost'
        if host_ids:
            host_obj = self.pool.get('ineco.report.config').browse(cr, uid, host_ids)[0]
            hostname = host_obj['host']            
            url = 'http://'+hostname+':8000/jasperserver/services/repository?wsdl'
            j = jasperclient.JasperClient(url,host_obj.report_user,host_obj.report_password)
            report_path = host_obj['report_id']
            if len(period_id) == 1:
                period_str = ' osp.id in (' + str(period_id[0]) +')'
            else:
                period_str = ' osp.id in '+ str(tuple(period_id))
            a = j.runReport(report_path, this.format,{'period_id': str(period_str)})
            this.name = "%s.%s" % (report_name, this.format)
            buf = StringIO()
            buf.write(a['data'])
            report = base64.encodestring(buf.getvalue())
            buf.close()
        else:
            raise osv.except_osv(_('Error !'),_('You have not config report ineco.logistic.summary in ineco.report.config!'))
        return self.write(cr, uid, ids, {'state':'get', 'report':report, 'name':this.name}, context=context)
        #return self.write(cr, uid, ids, {'report':report}, context=context)

    _name = "wizard.ineco.report.pivot.delivery.period.summary"
    _description = "Kitting Report"

    _columns = {
        'name': fields.char('Filename', 16, readonly=True),                
        'period_id': fields.many2many('omg.sale.period', 'report_category_rel', 'report_id', 'period_id', 'Periods'),
        'report': fields.binary('Report File'),
        'state': fields.selection( ( ('choose','choose'), ('get','get'), ) ),
        'format': fields.selection( ( ('csv','CSV File'), ('pdf','PDF File'), ('xls', 'Excel 2003')), 'File Format', required=True),        
    }
    _defaults = { 
        'state': lambda *a: 'choose',
        'name': lambda *a: 'delivery_summary_by_period.pdf',
        'format': 'pdf'
    }    


wizard_report_pivot_summary_delivery_by_period()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
