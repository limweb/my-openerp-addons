# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 INECO PARTNERSHIP LIMITED (<http://openerp.tititab.com>).
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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import fields, osv
from osv.orm import browse_record, browse_null
from tools.translate import _

class booking_checkprice_wizard(osv.osv_memory):
    
    _name = "booking.checkprice.wizard"
    _description = "Check sale reservation total price"
    _columns = {
    }

    def check_price(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record_ids = context and context.get('active_ids', False)
        for record_id in record_ids:
            contact_line_ids = self.pool.get('omg.sale.reserve.contact.line').search(cr, uid, [('contact_id','=',record_id)])
            for contact_line in self.pool.get('omg.sale.reserve.contact.line').browse(cr, uid, contact_line_ids):
                sql= "select f.id, f.name, f.list_price, count(*) as quantity from omg_sale_reserve_contact_line a " \
                    "join omg_sale_reserve_contact b on a.contact_id = b.id " \
                    "join omg_sale_reserve_contact_line_location c on a.id = c.contact_line_id " \
                    "join stock_location d on c.location_id = d.id " \
                    "join omg_sale_location_type e on d.location_type_id = e.id " \
                    "join product_template f on e.product_id = f.id " \
                    "join product_uom g on f.uom_id = g.id " \
                    "where a.id = %s " \
                    "group by " \
                    "  f.id, f.name, f.list_price"
                cr.execute(sql % (contact_line.id))
                for res in cr.dictfetchall():
                    delete_sql = "delete from omg_sale_reserve_contact_line_summary where product_id = '%s' and contact_line_id = %s "
                    cr.execute(delete_sql % (res['id'],contact_line.id))
                    product_line_obj = self.pool.get('omg.sale.reserve.contact.line.summary')
                    product_line_obj.create(cr, uid, 
                        { 
                            'name': res['name'],
                            'contact_line_id': contact_line.id,
                            'product_id': res['id'],
                            'product_qty': res['quantity'],
                            'sale_price': res['list_price']
                         })
            
        return {'type': 'ir.actions.act_window_close'}

booking_checkprice_wizard()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
