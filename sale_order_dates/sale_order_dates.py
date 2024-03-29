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

from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import fields, osv

class sale_order_dates(osv.osv):
    _inherit = 'sale.order'

    def _get_effective_date(self, cr, uid, ids, name, arg, context=None):
        res = {}
        dates_list = []
        for order in self.browse(cr, uid, ids, context=context):
            dates_list = []
            for pick in order.picking_ids:
                dates_list.append(pick.min_date)
            if dates_list:
                res[order.id] = min(dates_list)
            else:
                res[order.id] = False
        return res

    def _get_commitment_date(self, cr, uid, ids, name, arg, context=None):
        res = {}
        dates_list = []
        for order in self.browse(cr, uid, ids, context=context):
            dates_list = []
            for line in order.order_line:
                dt = datetime.strptime(order.date_order, '%Y-%m-%d') + relativedelta(days=line.delay or 0.0)
                dt_s = dt.strftime('%Y-%m-%d')
                dates_list.append(dt_s)
            if dates_list:
                res[order.id] = min(dates_list)
        return res

    _columns = {
        'commitment_date': fields.function(_get_commitment_date, method=True, store=True, type='date', string='Commitment Date', help="Date on which delivery of products is to be made."),
        'requested_date': fields.date('Requested Date', help="Date on which customer has requested for sales."),
        'effective_date': fields.function(_get_effective_date, method=True, type='date', store=True, string='Effective Date',help="Date on which picking is created."),
    }

sale_order_dates()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
