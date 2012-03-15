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

class wizard_ineco_stock_delivery_compute(osv.osv_memory):

    def act_cancel(self, cr, uid, ids, context=None):
        #self.unlink(cr, uid, ids, context)
        return {'type':'ir.actions.act_window_close' }

    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }

    def execute(self, cr, uid, ids, context=None):
        cron_ids = self.pool.get('ir.cron').search(cr, uid, [('model','=','ineco.stock.report')])
        if cron_ids:
            cron = self.pool.get('ir.cron').browse(cr, uid, cron_ids)[0]
            cron.write({'active':False})
        try:
            this = self.browse(cr, uid, ids)[0]
            if context is None:
                context = {}
            datas = {'ids': context.get('active_ids', [])}
            datas['model'] = 'wizard.ineco.stock.delivery.compute'
            datas['form'] = self.read(cr, uid, ids, context=context)[0]
            
            for field in datas['form'].keys():
                if isinstance(datas['form'][field], tuple):
                    datas['form'][field] = datas['form'][field][0]
            if datas['form']['date_delivery']:
                delivery_date = datas['form']['date_delivery'] 
                #POP-001
                product_id = datas['form']['product_id']
                cr.execute("""
                    select id from stock_picking
                    where state in ('draft','confirmed','assigned') and type = 'out' and ineco_delivery_date is not null
                    and ineco_delivery_date = '%s' and customer_product_id = '%s'
                    order by ineco_delivery_date, date_arrival
                """ %  (delivery_date, product_id) )
                dict1 = cr.dictfetchall()
                for row in dict1:
                   pick_obj =  self.pool.get('stock.picking').browse(cr, uid, row['id'])
                   if pick_obj.state == 'draft' :
                       pick_obj.draft_force_assign()
                   pick_obj.action_assign()
        finally:
            if cron_ids:
                cron = self.pool.get('ir.cron').browse(cr, uid, cron_ids)[0]
                cron.write({'active':True})
            
        return self.write(cr, uid, ids, {'state':'get', }, context=context)

    _name = "wizard.ineco.stock.delivery.compute"
    _description = "Compute delivery move from stock"

    _columns = {
        'date_delivery': fields.date('Delivery Date', required=True),
        #POP-001
        'product_id': fields.many2one('product.product', 'Customer Product', required=True),                
        'state': fields.selection( ( ('choose','choose'), ('get','get'), ) ),
    }
    
    _defaults = { 
        'state': lambda *a: 'choose',
    }    


wizard_ineco_stock_delivery_compute()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
