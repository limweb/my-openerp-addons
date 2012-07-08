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
        if not d:
            return ""
        else:
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
        user_obj = self.pool.get('res.users').browse(cr, uid, uid)
        if datas['ids'] :
            location_from_obj = self.pool.get('ineco.stock.report').browse(cr, uid, datas['ids'][0])
            location_to_obj = self.pool.get('ineco.stock.report').browse(cr, uid, datas['ids'][len(datas['ids'])-1])
            inventory_id = self.pool.get('stock.inventory').create(cr, uid,
                {'name': 'Adjust By '+user_obj.login + " ["+location_from_obj.location_dest_id.name+"..."+location_to_obj.location_dest_id.name+']',
                 'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                 }
            )
            for stock in self.pool.get('ineco.stock.report').browse(cr, uid, datas['ids']):
                line_id = self.pool.get('stock.inventory.line').create(cr, uid, 
                   { 'inventory_id': inventory_id,
                     'product_id': stock.product_id.id or False ,
                     'product_uom': stock.uom_id.id or False,
                     'location_id': stock.location_dest_id.id or False ,
                     'prod_lot_id': stock.lot_id.id or False,
                     'tracking_id': stock.tracking_id.id or False,
                     'product_qty': stock.qty, 
                     'before_qty': stock.qty,
                    }
                ) 
            mod_obj = self.pool.get('ir.model.data')
            res = mod_obj.get_object_reference(cr, uid, 'stock', 'view_inventory_form')
            res_id = res and res[1] or False,
            return {
                'name': 'Physical Inventory',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': list(res_id),
                'res_model': 'stock.inventory',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'res_id': inventory_id ,
            }  
        else:          
            return {'type':'ir.actions.act_window_close' }
    
    _name = "wizard.ineco.export.stock.counting"
    _description = "Export Stock Counting"

    _columns = {
        'name': fields.char('Filename', 16, readonly=True),       
        'report': fields.binary('Report File', readonly=True),
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
