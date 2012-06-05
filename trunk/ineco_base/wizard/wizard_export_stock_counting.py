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
import jasperclient
import base64
import csv
import codecs

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class wizard_ineco_export_stock_counting(osv.osv_memory):

    def act_cancel(self, cr, uid, ids, context=None):
        #self.unlink(cr, uid, ids, context)
        return {'type':'ir.actions.act_window_close' }

    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }

    def str_thai(self, d):
        if isinstance(d, basestring):
            d = d.replace('\n',' ').replace('\t',' ')
            try:
                d = d.encode('cp874')
            except:
                pass
            if d is False: d = None
        return d

    def export_report(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        if context is None:
            context = {}
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.ineco.stock.report'
        datas['form'] = self.read(cr, uid, ids, context=context)[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        location_obj = self.pool.get('stock.location')
        report = False
        stock_ids = location_obj.search(cr, uid, [('name','=','Stock')])
        if stock_ids:
            location_ids = location_obj.search(cr, uid, [('location_id','child_of',stock_ids)])
            if location_ids:
                
                try:
                    fp = StringIO()
                    writer = csv.writer(fp, quoting=csv.QUOTE_ALL)

                    for location in self.pool.get('stock.location').browse(cr, uid, sorted(location_ids)):
                        stock_ids = self.pool.get('ineco.stock.report').search(cr, uid, [('location_dest_id','=',location.id)])
                        for data in self.pool.get('ineco.stock.report').browse(cr, uid, stock_ids):
                            row = []
                            row.append(location.name.replace('\n',' ').replace('\t',' '))
                            row.append(self.str_thai(data.product_id.name))
                            row.append(self.str_thai(data.lot_id.name))
                            row.append(self.str_thai(data.tracking_id.name))
                            row.append(self.str_thai(data.uom_id.name))
                            row.append(data.qty)                
                            writer.writerow(row)
                        
                    fp.seek(0)
                    output = fp.read()
                    fp.close()
                    #report = base64.encodestring(output.getvalue())
                except IOError, (errno, strerror):
                    raise osv.except_osv(_("Operation failed\nI/O error")+"(%s)" % (errno,))                
                
        else:
            raise osv.except_osv(_('Error !'),_('"Stock", Name not found!'))

        return self.write(cr, uid, ids, {'state':'get', 'report':output, 'name':'report.csv'}, context=context)
    
    _name = "wizard.ineco.export.stock.counting"
    _description = "Export Stock Counting"

    _columns = {
        'name': fields.char('Filename', 16, readonly=True),       
        'report': fields.binary('Report File'),
        'check_zero': fields.boolean('Only Zero Quantity'),
        'check_less': fields.boolean('Only Quantity < 0'),         
        'state': fields.selection( ( ('choose','choose'), ('get','get'), ) ),
    }
    _defaults = { 
        'state': lambda *a: 'choose',
        'name': lambda *a: 'stock_counting.pdf',
        'check_zero': 0,
        'check_less': 0,
    }    

wizard_ineco_export_stock_counting()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
