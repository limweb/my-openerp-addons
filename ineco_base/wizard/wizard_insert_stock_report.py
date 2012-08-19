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
#19-08-2012        POP-001        Initial

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

class wizard_ineco_insert_stock_report(osv.osv_memory):

    def act_cancel(self, cr, uid, ids, context=None):
        #self.unlink(cr, uid, ids, context)
        return {'type':'ir.actions.act_window_close' }

    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }

    def execute(self, cr, uid, ids, context=None):
        select_sql = """
            select 
              srp.product_id,
              srp.location_id,
              srp.prodlot_id,
              round(sum(srp.qty),4) as qty,
              round(sum(srp.qty),4) as quantity
            from stock_report_prodlots srp
            join product_product pp on srp.product_id = pp.id
            left join stock_production_lot spl on srp.prodlot_id = spl.id
            where pp.active = True 
            group by
              srp.product_id,
              srp.location_id,
              srp.prodlot_id
            """
        cr.execute(select_sql)
        dict1 = cr.dictfetchall()
        for row in dict1:
            stock_report_obj = self.pool.get('ineco.stock.report')
            if row['product_id']:
                product = self.pool.get("product.template").browse(cr, uid, [row['product_id']])[0]
                product_wh = self.pool.get("product.product").browse(cr, uid, [row['product_id']])[0]
            lot = False
            if row['prodlot_id']:
                lot = self.pool.get('stock.production.lot').browse(cr, uid, [row['prodlot_id']])[0]
            new_data = {
                'product_id': row['product_id'],
                'uom_id': product.uom_id.id,
                'qty': row['qty'],
                'quantity': row['qty'],
                'lot_id': row['prodlot_id'] or False,
                'location_dest_id': row['location_id'],
                'warehouse_uom': product_wh.warehouse_uom.id,
                'date_input': lot and lot.date or False,
                'expired': lot and lot.date_expired or False,
            }
            new_id = stock_report_obj.create(cr, uid, new_data)
        
        return {'type':'ir.actions.act_window_close' }

    _name = "wizard.ineco.insert.stock.report"
    _description = "Insert Stock Report"

    _columns = {
        'state': fields.selection( ( ('choose','choose'), ('get','get'), ) ),
    }
    _defaults = { 
        'state': lambda *a: 'choose',
    }    

wizard_ineco_insert_stock_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
