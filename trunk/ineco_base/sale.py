# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

# 25-09-2012     POP-001    Add Stock Period ID

import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp

import netsvc


class sale_order(osv.osv):

    def _amount_line_tax(self, cr, uid, line, context=None):
        val = 0.0
        for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, line.price_unit * (1-(line.discount or 0.0)/100.0), line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            max_tax = 0 
            vat_type = True            
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
                for tax in line.tax_id:
                    max_tax = max(max_tax, tax.amount) 
                    vat_type = tax.include_base_amount = True
            if vat_type: #exclude tax
                res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val1 * max_tax)
            else: #include tax
                res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val1 * (max_tax * 100 / (100 + (max_tax * 100))))                                
            #res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    _name = 'sale.order'
    _inherit = 'sale.order'
    _description = 'Change tax calculation in sale order.'
    _columns = {
        'amount_untaxed': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax."),
        'amount_tax': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Taxes',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Total',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),      
    }
    
    def action_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        if context is None:
            context = {}
        sale_order_line_obj = self.pool.get('sale.order.line')
        proc_obj = self.pool.get('procurement.order')
        for sale in self.browse(cr, uid, ids, context=context):
            for pick in sale.picking_ids:
                if pick.state not in ('cancel'):
                    #if pick.state == 'done':
                    pick.action_done_draft()
                #pick.action_cancel()
                #if pick.state == 'cancel':
                #    for mov in pick.move_lines:
                #        proc_ids = proc_obj.search(cr, uid, [('move_id', '=', mov.id)])
                #        if proc_ids:
                #            for proc in proc_ids:
                #                wf_service.trg_validate(uid, 'procurement.order', proc, 'button_check', cr)
            for r in self.read(cr, uid, ids, ['picking_ids']):
                for pick in r['picking_ids']:
                    wf_service.trg_validate(uid, 'stock.picking', pick, 'button_cancel', cr)
            for inv in sale.invoice_ids:
                if inv.state not in ('draft', 'cancel'):
                    raise osv.except_osv(
                        _('Could not cancel this sales order !'),
                        _('You must first cancel all invoices attached to this sales order.'))
            for r in self.read(cr, uid, ids, ['invoice_ids']):
                for inv in r['invoice_ids']:
                    wf_service.trg_validate(uid, 'account.invoice', inv, 'invoice_cancel', cr)
            sale_order_line_obj.write(cr, uid, [l.id for l in  sale.order_line],
                    {'state': 'cancel'})
            message = _("The sales order '%s' has been cancelled.") % (sale.name,)
            self.log(cr, uid, sale.id, message)
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True
    
sale_order()

class sale_order_line(osv.osv):
    
    def _get_warehouse_qty(self, cr, uid, ids, field_name, arg, context=None):
        """ Gets stock of products for locations
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = 0
            if line.stock_period_id and line.order_id.shop_id and line.product_id :
                planning_ids = self.pool.get('stock.planning').search(cr, uid, [('warehouse_id','=',line.order_id.shop_id.warehouse_id.id),
                                                                 ('product_id','=',line.product_id.id),
                                                                 ('period_id','=',line.stock_period_id.id)])
                if planning_ids:
                    plan = self.pool.get('stock.planning').browse(cr, uid, planning_ids)[0]
                    if plan:
                        res[line.id] = plan.stock_start                         
        return res

    def _get_store_qty(self, cr, uid, ids, field_name, arg, context=None):
        """ Gets stock of products for locations
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        res = {}
        for line in self.browse(cr, uid, ids):            
            res[line.id] = 0
            warehouse_sql = """
                select id from stock_warehouse
                where lot_stock_id in (
                
                select sbl.location_id from sale_order so 
                join sale_order_line sol on so.id = sol.order_id
                join sale_branch_line sbl on so.id = sbl.sale_id
                where so.id = %s )
            """            
            cr.execute(warehouse_sql % (line.order_id.id))
            act_ids = map(lambda x: x[0], cr.fetchall())
            if act_ids and line.stock_period_id and line.product_id :
                    planning_ids = self.pool.get('stock.planning').search(cr, uid, [('warehouse_id','in',act_ids),
                                                                     ('product_id','=',line.product_id.id),
                                                                     ('period_id','=',line.stock_period_id.id)])
                    stock_all = 0
                    for data in self.pool.get('stock.planning').browse(cr, uid, planning_ids):
                        stock_all = stock_all + data.stock_start
                    res[line.id] = stock_all                       
        return res
    
    _inherit = "sale.order.line"
    _description="Add Stock Period In Sale Order Line"
    _columns = {
        #POP-001
        'stock_period_id': fields.many2one('stock.period'),
        'period_warehouse_qty': fields.function(_get_warehouse_qty, method=True, type="float", string="Warehouse Qty", digits_compute=dp.get_precision('Product UoM')),        
        'period_store_qty': fields.function(_get_store_qty, method=True, type="float", string="Store Qty", digits_compute=dp.get_precision('Product UoM')),        
    }

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
            
        if 'order_id' in vals:
            period_sql = """
                select
                  (select id from stock_period 
                   where date_start <= so.date_period_start and date_stop >= so.date_period_start) as stock_period_id
                from sale_order so 
                where so.id = %s
                """
            cr.execute(period_sql % (vals['order_id']))
            act_ids = map(lambda x: x[0], cr.fetchall())
            if act_ids:
                act_id = act_ids[0]
                vals.update({'stock_period_id': act_id })
        
        return super(sale_order_line, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        
        #Warning Date Period Start in OMG Module
        period_sql = """
            select
              (select id from stock_period 
               where date_start <= so.date_period_start and date_stop >= so.date_period_start) as stock_period_id
            from sale_order_line sol
            join sale_order so on sol.order_id = so.id
            where sol.id = %s
            """
        cr.execute(period_sql % (ids[0]))
        act_ids = map(lambda x: x[0], cr.fetchall())
        if act_ids:
            act_id = act_ids[0]
            vals.update({'stock_period_id': act_id })
            
        return super(sale_order_line, self).write(cr, uid, ids, vals, context=context)
    
sale_order_line()
