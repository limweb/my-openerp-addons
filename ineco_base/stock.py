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

# Date             ID         Message
# 15-12-2011       POP-001    Create new Class ineco.stock.report
# 21-12-2011       POP-002    Change Query in ineco.stock.report
# 23-12-2011       POP-003    Change Auto Picking on Delivery Order
# 28-12-2011       POP-004    Add Class ineco.stock.tracking.line
# 30-12-2011       POP-005    Change Schedule find location before Delivery
# 11-01-2012       POP-006    Change ineco.stock.report
# 17-01-2012       POP-007    Add Check Qty before internal move
# 27-01-2012       POP-008    Add New Sequence by Stock Journal
#                  POP-009    Move ineco.stock.sticker to product.py
# 28-01-2012       POP-010    Move ineco.stock.keeping.method to product.py
# 15-01-2012       POP-011    Create Query query.ineco.stock.report 
# 20-02-2012       POP-012    Create ienco.stock.barcode.delivery
# 08-03-2012       POP-013    Make performance auto picking
# 10-03-2012       POP-014    Change Split in Auto Picking -> Valid by Do it Again
# 14-03-2012       POP-015    Change way to force compute with delivery
# 16-03-2012       POP-015    Change Set to Confirm -> Set To Draft
# 30-03-2012       POP-016    Create ineco.stock.barcode.move
# 05-04-2012       POP-017    Add Return Columns in Stock Picking
# 08-06-2012       POP-018    Change Date -> DateTime in Stock Move Barcode Delivery
# 22-06-2012       POP-019    Add Unique Name of Production Lot
#                  POP-020    Add Product ID in Stock Packing
# 26-06-2012       POP-021    Add Button Problem
# 29-06-2012       POP-022    Change Default Warehouse UOM
# 07-07-2012       POP-023    Add Before Qty in Physical Inventory
# 18-07-2012       POP-024    Remove Unique Index in stock.production.lot
# 24-07-2012       POP-025    Add Picking Do Parial
# 16-08-2012       POP-026    Default Stock Picking Order by Date desc, name desc
# 19-08-2012       POP-027    Change Default Get Stock In Stock Production Lot
# 22-08-2012       POP-028    Change ineco.stock.report on Digits UOM from Product UOM Digits
# 20-09-2012       POP-029    Add Patial/Full in Stock Move
# 24-09-2012       POP-030    Change Stock_Report.Qty -> Stock_Report.Available in Physical Inventory
#                  POP-031    Add Schedule Correct Stock Report 
# 25-09-2012       POP-032    Add Stock Move Date Done
#                  POP-033    Add Stock Period in Stock Move
# 30-09-2012       POP-034    Add Type in Stock Move
#                  POP-035    Add schedule_update_type
# 10-10-2012       POP-036    Add On Change Full_Qty/Partial_Qty

import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp
import netsvc

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from operator import itemgetter
from itertools import groupby

class stock_inventory(osv.osv):
    
    _name = "stock.inventory"
    _inherit = "stock.inventory"
    _description = "Stock Inventory"    

    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        account = self.browse(cr, uid, id, context=context)
        new_child_ids = []
        if not default:
            default = {}
        default = default.copy()
        default['name'] = (account['name'] or '') + ' (copy)'
        default['date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        default['move_ids'] = False
        new_id = super(stock_inventory, self).copy(cr, uid, id, default, context=context)
        if new_id:
            inv_obj = self.browse(cr, uid, new_id, context=context)
            for line in inv_obj.inventory_line_id:
                stock_report_ids = self.pool.get('ineco.stock.report').search(cr, uid, 
                    [('location_dest_id','=',line.location_id.id),('product_id','=',line.product_id.id),('qty','!=',0)])
                if stock_report_ids:
                    stock = self.pool.get('ineco.stock.report').browse(cr, uid, stock_report_ids)[0]
                    line.write({'before_qty':stock.qty,'product_qty': stock.qty})                
                else:
                    line.write({'before_qty':0,'product_qty': 0})            
        return new_id

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirm the inventory and writes its finished date
        @return: True
        """
        if context is None:
            context = {}
        # to perform the correct inventory corrections we need analyze stock location by
        # location, never recursively, so we use a special context
        product_context = dict(context, compute_child=False)

        location_obj = self.pool.get('stock.location')
        for inv in self.browse(cr, uid, ids, context=context):
            move_ids = []
            for line in inv.inventory_line_id:
                pid = line.product_id.id
                product_context.update(uom=line.product_uom.id,date=inv.date)
                if line.tracking_id and line.prod_lot_id:
                    stock_report_ids = self.pool.get('ineco.stock.report').search(cr, uid, 
                        [('lot_id','=',line.prod_lot_id.id),('tracking_id','=',line.tracking_id.id)])
                elif line.prod_lot_id:
                    stock_report_ids = self.pool.get('ineco.stock.report').search(cr, uid, 
                        [('location_dest_id','=',line.location_id.id),('product_id','=',line.product_id.id),('lot_id','=',line.prod_lot_id.id)])
                else:
                    stock_report_ids = self.pool.get('ineco.stock.report').search(cr, uid, 
                        [('location_dest_id','=',line.location_id.id),('product_id','=',line.product_id.id)])
                amount = 0
                if stock_report_ids:
                    stock_report = self.pool.get('ineco.stock.report').browse(cr, uid, stock_report_ids)[0]
                    #amount = stock_report.qty
                    #POP-030
                    amount = stock_report.available                    
                    #amount = location_obj._product_get(cr, uid, line.location_id.id, [pid], product_context)[pid]

                change = line.product_qty - amount
                lot_id = False
                if line.prod_lot_id:                
                    lot_id =  line.prod_lot_id.id 
                if change:
                    full_qty = round(change // round(1/line.full_uom.factor)) or 0.0
                    partial_qty = round(change - round( (full_qty / line.full_uom.factor), 10))
                    
                    product_template = self.pool.get('product.template').browse(cr ,uid, [line.product_id.id] )[0]
                    location_id = product_template.property_stock_inventory.id
                    #location_id = line.product_id.product_tmpl_id.property_stock_inventory.id
                    value = {
                        'name': 'INV:' + str(line.inventory_id.id) + ':' + line.inventory_id.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'prodlot_id': lot_id,
                        'tracking_id': line.tracking_id.id,
                        'date': inv.date,
                        'full_uom': line.full_uom.id,
                        'partial_uom': line.partial_uom.id,
                    }
                    if change > 0:
                        value.update( {
                            'product_qty': change,
                            'full_qty': full_qty,
                            'partial_qty': partial_qty,
                            'location_id': location_id,
                            'location_dest_id': line.location_id.id,
                        })
                    else:
                        value.update( {
                            'product_qty': -change,
                            'location_id': line.location_id.id,
                            'location_dest_id': location_id,
                            'full_qty': -full_qty,
                            'partial_qty': -partial_qty,
                        })
                    #if lot_id:
                    #    value.update({
                    #        'prodlot_id': lot_id,
                    #        #'product_qty': line.product_qty
                    #    })
                    move_ids.append(self._inventory_line_hook(cr, uid, line, value))
            message = _("Inventory '%s' is done.") %(inv.name)
            self.log(cr, uid, inv.id, message)
            self.write(cr, uid, [inv.id], {'state': 'confirm', 'move_ids': [(6, 0, move_ids)]})
        return True
    
stock_inventory()

class stock_inventory_line(osv.osv):
    _name = "stock.inventory.line"
    _inherit = "stock.inventory.line"
    _description = "Inventory Line"
    _columns = {
        'uom_category_id': fields.many2one('product.uom.categ', 'UOM Category', ondelete="restrict"),
        'tracking_id': fields.many2one('stock.tracking', 'Pack'),
        #POP-023
        'before_qty': fields.float('Before Qty'),
        #POP-029
        'partial_uom': fields.many2one('product.uom', 'Partial UOM'),
        'partial_qty': fields.integer('Partial Qty'),
        'full_uom': fields.many2one('product.uom', 'Full UOM'),
        'full_qty': fields.integer('Full Qty'),        
    }
    _defaults = {
        'before_qty': 0,
        'partial_qty': 0,
        'full_qty': 0,
    }

    def on_change_product_id(self, cr, uid, ids, location_id, product, uom=False, to_date=False):
        if not product:
            return {}
        uom_categ_id = None
        partial_uom = False
        full_uom = False
        if not uom:
            prod = self.pool.get('product.product').browse(cr, uid, [product], {'uom': uom})[0]
            uom = prod.uom_id.id
            uom_categ_id = prod.uom_id.category_id.id
            partial_uom = prod.uom_id.id or False
            full_uom = prod.warehouse_uom.id or False
        stock_location_ids = self.pool.get("stock.location").search(cr, uid, [('name','=','Stock'),('location_id','=',1)])
        stock_report_ids = self.pool.get('ineco.stock.report').search(cr, uid, [('location_dest_id','=',location_id),('product_id','=',product),('location_dest_id','child_of',stock_location_ids),('qty','!=',0)])
        lot_id = False
        tracking_id = False
        amount = 0
        partial_qty = 0.0
        full_qty = 0.0
        if stock_report_ids:
            stock_report = self.pool.get('ineco.stock.report').browse(cr, uid, stock_report_ids)[0]
            amount = stock_report.qty
            lot_id = stock_report.lot_id.id
            tracking_id = stock_report.tracking_id.id
            partial_uom = stock_report.partial_uom.id or False
            full_uom = stock_report.full_uom.id or False
            partial_qty = stock_report.partial_qty or 0.0
            full_qty = stock_report.full_qty or 0.0
        #amount = self.pool.get('stock.location')._product_get(cr, uid, location_id, [product], {'uom': uom, 'to_date': to_date})[product]
        result = {'before_qty': amount, 'product_qty': amount, 
                  'product_uom': uom,'uom_category_id': uom_categ_id,
                  'tracking_id':tracking_id,'prod_lot_id':lot_id,
                  'partial_uom': partial_uom,
                  'full_uom': full_uom,
                  'partial_qty': partial_qty,
                  'full_qty': full_qty,
                   }
        return {'value': result}

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
            
        if 'product_id' in vals and 'partial_qty' in vals and 'partial_uom' in vals and 'full_qty' in vals and 'full_uom' in vals :            
            uom_obj = self.pool.get('product.uom')
            partial_uom = self.pool.get('product.uom').browse(cr, uid, vals['partial_uom'])
            full_uom = self.pool.get('product.uom').browse(cr, uid, vals['full_uom'])
            
            partial_qty = vals['partial_qty']
            full_qty = vals['full_qty']

            qty1 = uom_obj._compute_qty_obj(cr, uid, partial_uom, partial_qty, partial_uom, context=context ) or 0.0
            qty2 = uom_obj._compute_qty_obj(cr, uid, full_uom, full_qty, partial_uom, context=context ) or 0.0
            
            vals['product_qty'] = qty1+qty2
            
        return super(stock_inventory_line, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        if 'product_id' in vals and 'partial_qty' in vals and 'partial_uom' in vals and 'full_qty' in vals and 'full_uom' in vals :
            uom_obj = self.pool.get('product.uom')
            
            partial_uom = self.pool.get('product.uom').browse(cr, uid, vals['partial_uom'])
            full_uom = self.pool.get('product.uom').browse(cr, uid, vals['full_uom'])
            
            partial_qty = vals['partial_qty']
            full_qty = vals['full_qty']

            qty1 = uom_obj._compute_qty_obj(cr, uid, partial_uom, partial_qty, partial_uom, context=context ) or 0.0
            qty2 = uom_obj._compute_qty_obj(cr, uid, full_uom, full_qty, partial_uom, context=context ) or 0.0
            
            vals['product_qty'] = qty1+qty2
            
        return super(stock_inventory_line, self).write(cr, uid, ids, vals, context=context)

stock_inventory_line()

class stock_move(osv.osv):

    def _get_warehouse_qty(self, cr, uid, ids, field_name, arg, context=None):
        """ Gets stock of products for locations
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        res = {}
        wids = self.pool.get('stock.warehouse').search(cr, uid, [('allow_counting','!=',False)], context=context)
        for line in self.browse(cr, uid, ids):
            res[line.id] = 0            
            if line.stock_period_id and wids and line.product_id :
                planning_ids = self.pool.get('stock.planning').search(cr, uid, [('warehouse_id','in',wids),
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
                  select location_dest_id 
                  from stock_move sm 
                  where sm.id = %s )
            """            
            cr.execute(warehouse_sql % (line.id))
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

    def _ineco_default_location_destination(self, cr, uid, context=None):
        """ Gets default address of partner for destination location
        @return: Address id or False
        """
        if context is None:
            context = {}
        if context.get('move_line', []):
            if context['move_line'][0]:
                if isinstance(context['move_line'][0], (tuple, list)):
                    return context['move_line'][0][2] and context['move_line'][0][2].get('location_dest_id',False)
                else:
                    move_list = self.pool.get('stock.move').read(cr, uid, context['move_line'][0], ['location_dest_id'])
                    return move_list and move_list['location_dest_id'][0] or False
        if context.get('address_out_id', False):
            property_out = self.pool.get('res.partner.address').browse(cr, uid, context['address_out_id'], context).partner_id.property_stock_customer
            return property_out and property_out.id or False
        return False
    
    _name="stock.move"
    _inherit="stock.move"
    _columns={
        'category_id': fields.many2one('product.uom.categ', 'UOM Category', ondelete="restrict"),
        'warehouse_uom': fields.many2one('product.uom', 'Warehouse Unit of Measure'),
        'warehouse_qty': fields.integer('Warehouse Qty'),        
        'warehouse_diff': fields.integer('Warehouse Diff'),
        #POP-029
        'partial_uom': fields.many2one('product.uom', 'Partial UOM'),
        'partial_qty': fields.integer('Partial Qty'),
        'full_uom': fields.many2one('product.uom', 'Full UOM'),
        'full_qty': fields.integer('Full Qty'),        
        #POP-032 
        'ineco_date_complete' : fields.datetime('Date Complete'),
        'stock_product_qty': fields.float('Default Qty', digits_compute=dp.get_precision('Product UoM'), states={'done': [('readonly', True)]}),
        #POP-033
        'stock_period_id': fields.many2one('stock.period'),
        'period_warehouse_qty': fields.function(_get_warehouse_qty, method=True, type="float", string="Warehouse Qty", digits_compute=dp.get_precision('Product UoM')),        
        'period_store_qty': fields.function(_get_store_qty, method=True, type="float", string="Store Qty", digits_compute=dp.get_precision('Product UoM')),
        #POP-034
        'type': fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('internal', 'Internal')], 'Shipping Type', required=True, select=True, help="Shipping type specify, goods coming in or going out."),
    }

    _defaults = {
        'location_dest_id': _ineco_default_location_destination,
        'partial_qty': 0,
        'full_qty': 0,
    }

    #POP-035
    def schedule_update_type(self, cr, uid, context=None):
        stock_move_ids = self.pool.get('stock.move').search(cr, uid, [('type','=',False)])
        for line in self.pool.get('stock.move').browse(cr, uid, stock_move_ids):
            if line.picking_id:
                line.write({'type':line.picking_id.type})

    #POP-022 Change Default Warehouse UOM
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if 'product_id' in vals and 'product_qty' in vals and 'product_uom' in vals and 'partial_qty' in vals and 'partial_uom' in vals and 'full_qty' in vals and 'full_uom' in vals :
            uom_obj = self.pool.get('product.uom')
            #product_ids = self.pool.get("product.product").search(cr, uid, [('id','=',vals['product_id'])])
            #warning product outsize your company
            
            product_obj = self.pool.get('product.product').browse(cr, uid, vals['product_id'])
            product_tmpl_obj = self.pool.get('product.template').browse(cr, uid, vals['product_id'])
            default_uom_id = product_tmpl_obj.uom_id.id
            if product_obj.warehouse_uom:
                warehouse_uom_id = product_obj.warehouse_uom.id
            else:
                warehouse_uom_id = default_uom_id
                
            product_uom = self.pool.get('product.uom').browse(cr, uid, vals['product_uom'])
            partial_uom = self.pool.get('product.uom').browse(cr, uid, vals['partial_uom'])
            full_uom = self.pool.get('product.uom').browse(cr, uid, vals['full_uom'])
            
            product_qty = vals['product_qty']
            partial_qty = vals['partial_qty']
            full_qty = vals['full_qty']
            
            qty1 = uom_obj._compute_qty_obj(cr, uid, partial_uom, partial_qty, partial_uom, context=context ) or 0.0
            qty2 = uom_obj._compute_qty_obj(cr, uid, full_uom, full_qty, partial_uom, context=context ) or 0.0
            
            if qty1+qty2 <> product_qty:
                raise osv.except_osv(_('Error !'), _('Quantity unexceptable.'))
            
            warehouse_qty = product_qty
            diff = 0
            
            if warehouse_uom_id and product_obj.warehouse_uom:
                warehouse_qty = uom_obj._compute_qty_obj(cr, uid, product_uom , 
                    product_qty, product_obj.warehouse_uom, context=context )
            vals.update({'warehouse_uom': warehouse_uom_id,'warehouse_qty': warehouse_qty, 'category_id':product_uom.category_id.id}) #'warehouse_diff': diff

        if 'date_expected' in vals:
            period_sql = """
                select id from stock_period where date_start <= '%s' and date_stop >= '%s'
                """
            cr.execute(period_sql % (vals['date_expected'],vals['date_expected']))
            act_ids = map(lambda x: x[0], cr.fetchall())
            if act_ids:
                act_id = act_ids[0]
                vals.update({'stock_period_id': act_id })
                
        if 'product_id' in vals and 'product_qty' in vals and 'product_uom' in vals and not ('partial_qty' in vals) and not ('partial_uom' in vals) and not ('full_qty' in vals) and not ('full_uom' in vals) :
            uom_obj = self.pool.get('product.uom')
            product_obj = self.pool.get('product.product').browse(cr, uid, vals['product_id'])
            if product_obj:
                vals['partial_qty'] = vals['product_qty']
                vals['partial_uom'] = vals['product_uom']
                vals['full_qty'] = 0.0
                vals['full_uom'] = product_obj.warehouse_uom and product_obj.warehouse_uom.id    
                                    
        return super(stock_move, self).create(cr, uid, vals, context)

    #POP-022
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        if 'product_id' in vals and 'product_qty' in vals and 'product_uom' in vals and 'partial_qty' in vals and 'partial_uom' in vals and 'full_qty' in vals and 'full_uom' in vals :
            uom_obj = self.pool.get('product.uom')
            
            product_uom = self.pool.get('product.uom').browse(cr, uid, vals['product_uom'])
            partial_uom = self.pool.get('product.uom').browse(cr, uid, vals['partial_uom'])
            full_uom = self.pool.get('product.uom').browse(cr, uid, vals['full_uom'])
            
            product_qty = vals['product_qty']
            partial_qty = vals['partial_qty']
            full_qty = vals['full_qty']

            qty1 = uom_obj._compute_qty_obj(cr, uid, partial_uom, partial_qty, partial_uom, context=context ) or 0.0
            qty2 = uom_obj._compute_qty_obj(cr, uid, full_uom, full_qty, partial_uom, context=context ) or 0.0
            
            if qty1+qty2 <> product_qty:
                raise osv.except_osv(_('Error !'), _('Quantity unexceptable.'))
        
        if not isinstance(ids,list):
            ids = [ids]
        for sm in self.pool.get('stock.move').browse(cr, uid, ids):
            if sm.picking_id and not ('type' in vals) : 
                vals.update({'type':sm.picking_id.type})
            uom_obj = self.pool.get('product.uom')
            product_obj = False
            product_tmpl_obj = False
            if 'product_id' in vals:
                product_obj = self.pool.get('product.product').browse(cr, uid, vals['product_id'])
                product_tmpl_obj = self.pool.get('product.template').browse(cr, uid, vals['product_id'])
            else:
                product_obj = sm.product_id
                product_tmpl_obj = self.pool.get('product.template').browse(cr, uid, product_obj.id)
            default_uom = product_tmpl_obj.uom_id
            warehouse_uom_id = product_obj.warehouse_uom.id
            product_uom = False
            if 'product_uom' in vals:
                product_uom =  self.pool.get('product.uom').browse(cr, uid, vals['product_uom'])
            else:
                product_uom = sm.product_uom
            if 'product_qty' in vals:
                product_qty = vals['product_qty']
            else:
                product_qty = sm.product_qty or 0.0
            warehouse_qty = product_qty
            if warehouse_uom_id:
                warehouse_qty = uom_obj._compute_qty_obj(cr, uid, product_uom , 
                    product_qty, product_obj.warehouse_uom, context=context )
            if 'prodlot_id' in vals:
                lot_id = vals['prodlot_id']
                
            else:
                lot_id = sm.prodlot_id.id or False 
            date_input = False
            date_expired = False
            if lot_id:
                lot_obj = self.pool.get('stock.production.lot').browse(cr, uid, [lot_id])[0]
                date_input = lot_obj.date
                date_expired = lot_obj.date_expired
            
            if 'tracking_id' in vals:
                tracking_id = vals['tracking_id'] 
            else:
                tracking_id = sm.tracking_id.id or False
            if 'location_id' in vals:
                location_id = vals['location_id'] 
            else:
                location_id = sm.location_id.id or False
            if 'location_dest_id' in vals:
                location_dest_id = vals['location_dest_id'] 
            else:
                location_dest_id = sm.location_dest_id.id or False
            state_last = sm.state
            if 'state' in vals:
                state_current = vals['state'] 
            else:
                state_current = sm.state or False
            update_qty = uom_obj._compute_qty_obj(cr, uid, product_uom, product_qty, default_uom)
            #? -> done <> 'done' -> 'done' +
            #done -> ? <> 'done' -> 'done' -
            if state_current and (state_current == 'done' or state_last == 'done'):
                location_source_stock_ids = self.pool.get('ineco.stock.report').search(cr, uid, 
                    [('product_id','=',product_obj.id),
                     ('lot_id','=',lot_id or False),
                     ('tracking_id','=',tracking_id or False),
                     ('location_dest_id','=',location_id)])
                location_dest_stock_ids = self.pool.get('ineco.stock.report').search(cr, uid, 
                    [('product_id','=',product_obj.id),
                     ('lot_id','=',lot_id or False),
                     ('tracking_id','=',tracking_id or False),
                     ('location_dest_id','=',location_dest_id)])
                
                #Stock Issue
                if state_current == 'done' and state_last <> 'done':  
                    if location_source_stock_ids:  
                        source_obj = self.pool.get('ineco.stock.report').browse(cr, uid, location_source_stock_ids)[0]
                        update_warehouse_qty = uom_obj._compute_qty_obj(cr, uid, default_uom , 
                            source_obj.qty-update_qty, product_obj.warehouse_uom, context=context )
                        source_obj.write({'qty':source_obj.qty-update_qty,'warehouse_qty':update_warehouse_qty})
                        #source_obj.write({'qty':source_obj.available})
                    else:
                        update_warehouse_qty = uom_obj._compute_qty_obj(cr, uid, default_uom , 
                            -update_qty, product_obj.warehouse_uom, context=context )
                        source_obj_id = self.pool.get('ineco.stock.report').create(cr, uid, 
                            { 
                             'product_id': product_obj.id,
                             'lot_id': lot_id or False,
                             'tracking_id': tracking_id or False,
                             'location_dest_id': location_id or False,
                             'qty': -update_qty or 0.0,
                             'quantity': -update_qty or 0.0,
                             'uom_id': default_uom.id or False,
                             'warehouse_qty': update_warehouse_qty or 0.0,
                             'warehouse_uom': product_obj.warehouse_uom.id or False,
                             'date_input': date_input or False,
                             'expired': date_expired or False,
                             #POP-029
                             'partial_qty':sm.partial_qty,
                             'partial_uom':sm.partial_uom.id,
                             'full_qty':sm.full_qty,
                             'full_uom':sm.full_uom.id,
                            })
                    if location_dest_stock_ids:
                        destination_obj = self.pool.get('ineco.stock.report').browse(cr, uid, location_dest_stock_ids)[0]
                        update_warehouse_qty = uom_obj._compute_qty_obj(cr, uid, default_uom , 
                            destination_obj.qty+update_qty, product_obj.warehouse_uom, context=context )
                        destination_obj.write({'qty': destination_obj.qty+update_qty,'warehouse_qty':update_warehouse_qty})
                        #destination_obj.write({'qty': destination_obj.available})
                    else:
                        update_warehouse_qty = uom_obj._compute_qty_obj(cr, uid, default_uom , 
                            update_qty, product_obj.warehouse_uom, context=context )
                        destination_obj_id = self.pool.get('ineco.stock.report').create(cr, uid, 
                            { 
                             'product_id': product_obj.id,
                             'lot_id': lot_id or False,
                             'tracking_id': tracking_id or False,
                             'location_dest_id': location_dest_id or False,
                             'qty': update_qty or 0.0,
                             'quantity': update_qty or 0.0,
                             'uom_id': default_uom.id or False,
                             'warehouse_qty': update_warehouse_qty or 0.0,
                             'warehouse_uom': product_obj.warehouse_uom.id or False,
                             'date_input': date_input or False,
                             'expired': date_expired or False,
                             #POP-029
                             'partial_qty':sm.partial_qty,
                             'partial_uom':sm.partial_uom.id,
                             'full_qty':sm.full_qty,
                             'full_uom':sm.full_uom.id,
                            })
                
                #Stock Done
                if state_current <> 'done' and state_last == 'done':
                    if location_source_stock_ids:
                        source_obj = self.pool.get('ineco.stock.report').browse(cr, uid, location_source_stock_ids)[0]
                        update_warehouse_qty = uom_obj._compute_qty_obj(cr, uid, default_uom, 
                            source_obj.qty + update_qty, product_obj.warehouse_uom, context=context )
                        source_obj.write({'qty':source_obj.qty + update_qty, 'warehouse_qty': update_warehouse_qty})
                        #source_obj.write({'qty':source_obj.available})
                    else:
                        update_warehouse_qty = uom_obj._compute_qty_obj(cr, uid, default_uom, 
                            update_qty, product_obj.warehouse_uom, context=context )
                        source_obj_id = self.pool.get('ineco.stock.report').create(cr, uid, 
                            { 
                             'product_id': product_obj.id,
                             'lot_id': lot_id or False,
                             'tracking_id': tracking_id or False,
                             'location_dest_id': location_id or False,
                             'qty': update_qty or 0.0,
                             'quantity': update_qty or 0.0,
                             'uom_id': default_uom.id or False,
                             'warehouse_qty': update_warehouse_qty or 0.0,
                             'warehouse_uom': product_obj.warehouse_uom.id or False,
                             'date_input': date_input or False,
                             'expired': date_expired or False,
                             #POP-029
                             'partial_qty':sm.partial_qty,
                             'partial_uom':sm.partial_uom.id,
                             'full_qty':sm.full_qty,
                             'full_uom':sm.full_uom.id,
                            })
                    if location_dest_stock_ids:
                        destination_obj = self.pool.get('ineco.stock.report').browse(cr, uid, location_dest_stock_ids)[0]
                        update_warehouse_qty = uom_obj._compute_qty_obj(cr, uid, default_uom , 
                           destination_obj.qty-update_qty, product_obj.warehouse_uom, context=context )
                        if state_current == 'cancel' and destination_obj.qty-update_qty < 0:
                            pass
                        else:
                            destination_obj.write({'qty': destination_obj.qty-update_qty,'warehouse_qty':update_warehouse_qty})
                        #destination_obj.write({'qty': destination_obj.available})

                    else:
                        update_warehouse_qty = uom_obj._compute_qty_obj(cr, uid, default_uom , 
                           -update_qty, product_obj.warehouse_uom, context=context )
                        destination_obj_id = self.pool.get('ineco.stock.report').create(cr, uid, 
                            { 
                             'product_id': product_obj.id,
                             'lot_id': lot_id or False,
                             'tracking_id': tracking_id or False,
                             'location_dest_id': location_dest_id or False,
                             'qty': -update_qty or 0.0,
                             'quantity': -update_qty or 0.0,
                             'uom_id': default_uom.id or False,
                             'warehouse_qty': update_warehouse_qty or 0.0,
                             'warehouse_uom': product_obj.warehouse_uom.id or False,
                             'date_input': date_input or False,
                             'expired': date_expired or False,
                             #POP-029
                             'partial_qty':sm.partial_qty,
                             'partial_uom':sm.partial_uom.id,
                             'full_qty':sm.full_qty,
                             'full_uom':sm.full_uom.id,
                            })
                vals.update({'warehouse_uom': warehouse_uom_id,'warehouse_qty': warehouse_qty}) #'warehouse_diff': diff
            #POP-032 
            if 'state' in vals:
                state_current = vals['state'] 
                if state_current == 'done':
                    vals.update({'ineco_date_complete': time.strftime('%Y-%m-%d %H:%M:%S')})
                else:
                    vals.update({'ineco_date_complete': False})
            else:
                vals.update({'ineco_date_complete': False})
            
            vals.update({'stock_product_qty': update_qty })
            
            #POP-033
            period_sql = """
                select
                  (select id from stock_period 
                   where date_start <= sm.date_expected and date_stop >= sm.date_expected) as stock_period_id
                from stock_picking sp
                join stock_move sm on sp.id = sm.picking_id
                where sm.id = %s 
                """
            cr.execute(period_sql % (sm.id))
            act_ids = map(lambda x: x[0], cr.fetchall())
            if act_ids:
                act_id = act_ids[0]
                vals.update({'stock_period_id': act_id })

        return super(stock_move, self).write(cr, uid, ids, vals, context=context)
    
    #POP-036
    def onchange_new_quantity(self, cr, uid, ids, partial_uom, partial_qty, full_uom, full_qty, context=None):
        result = {}
        if context is None:
            context = {}
        if partial_uom and full_uom:
            uom_obj = self.pool.get('product.uom')
            partial_uom = self.pool.get('product.uom').browse(cr, uid, [partial_uom])[0]
            full_uom = self.pool.get('product.uom').browse(cr, uid, [full_uom])[0]
            qty1 = uom_obj._compute_qty_obj(cr, uid, partial_uom, partial_qty, partial_uom, context=context ) or 0.0
            qty2 = uom_obj._compute_qty_obj(cr, uid, full_uom, full_qty, partial_uom, context=context ) or 0.0            
            result = {'product_qty':qty1+qty2,'product_uos_qty':qty1+qty2}
        
        return {'value': result}
    
    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False,loc_dest_id=False, address_id=False):
        """ On change of product id, if finds UoM, UoS, quantity and UoS quantity.
        @param prod_id: Changed Product id
        @param loc_id: Source location id
        @param loc_id: Destination location id
        @param address_id: Address id of partner
        @return: Dictionary of values
        """
        if not prod_id:
            return {}
        lang = False
        if address_id:
            addr_rec = self.pool.get('res.partner.address').browse(cr, uid, address_id)
            if addr_rec:
                lang = addr_rec.partner_id and addr_rec.partner_id.lang or False
        ctx = {'lang': lang}

        product = self.pool.get('product.product').browse(cr, uid, [prod_id], context=ctx)[0]
        uos_id  = product.uos_id and product.uos_id.id or False
        result = {
            'product_uom': product.uom_id.id,
            'product_uos': uos_id,
            'product_qty': 1.00,
            'category_id': product.uom_id.category_id.id,
            'product_uos_qty' : self.pool.get('stock.move').onchange_quantity(cr, uid, ids, prod_id, 1.00, product.uom_id.id, uos_id)['value']['product_uos_qty']
        }
        #POP-029
        if product:
            result['partial_uom'] = product.uom_id.id
            result['full_uom'] = product.warehouse_uom.id or False
        if not ids:
            result['name'] = product.partner_ref
        if loc_id:
            result['location_id'] = loc_id
        if loc_dest_id:
            result['location_dest_id'] = loc_dest_id
        return {'value': result}

           
stock_move()

class stock_picking(osv.osv):
    
    _inherit = 'stock.picking'
    _columns = {
        'ineco_delivery_date': fields.date('Delivery Date'),
        'ineco_request_user_id': fields.many2one('res.users', 'Requested By'),
        #POP-017
        'ineco_return': fields.boolean('Return'),
    }
    
    _defaults = {
        'ineco_request_user_id': lambda self, cr, uid, context: uid,
    }
    
    #POP-026
    _order = "date desc, min_date desc, name desc"
    
    #POP-025
    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        """ Makes partial picking and moves done.
        @param partial_datas : Dictionary containing details of partial picking
                          like partner_id, address_id, delivery_date,
                          delivery moves with product_id, product_qty, uom
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        else:
            context = dict(context)
        res = {}
        move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.product')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        sequence_obj = self.pool.get('ir.sequence')
        wf_service = netsvc.LocalService("workflow")
        for pick in self.browse(cr, uid, ids, context=context):
            new_picking = None
            complete, too_many, too_few = [], [], []
            move_product_qty = {}
            prodlot_ids = {}
            product_avail = {}
            for move in pick.move_lines:
                if move.state in ('done', 'cancel'):
                    continue
                partial_data = partial_datas.get('move%s'%(move.id), {})
                product_qty = partial_data.get('product_qty',0.0)
                move_product_qty[move.id] = product_qty
                product_uom = partial_data.get('product_uom',False)
                product_price = partial_data.get('product_price',0.0)
                product_currency = partial_data.get('product_currency',False)
                prodlot_id = partial_data.get('prodlot_id')
                prodlot_ids[move.id] = prodlot_id
                if move.product_qty == product_qty:
                    complete.append(move)
                elif move.product_qty > product_qty:
                    too_few.append(move)
                else:
                    too_many.append(move)

                # Average price computation
                if (pick.type == 'in') and (move.product_id.cost_method == 'average'):
                    product = product_obj.browse(cr, uid, move.product_id.id)
                    move_currency_id = move.company_id.currency_id.id
                    context['currency_id'] = move_currency_id
                    qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product.uom_id.id)

                    if product.id in product_avail:
                        product_avail[product.id] += qty
                    else:
                        product_avail[product.id] = product.qty_available

                    if qty > 0:
                        new_price = currency_obj.compute(cr, uid, product_currency,
                                move_currency_id, product_price)
                        new_price = uom_obj._compute_price(cr, uid, product_uom, new_price,
                                product.uom_id.id)
                        if product.qty_available <= 0:
                            new_std_price = new_price
                        else:
                            # Get the standard price
                            amount_unit = product.price_get('standard_price', context)[product.id]
                            new_std_price = ((amount_unit * product_avail[product.id])\
                                + (new_price * qty))/(product_avail[product.id] + qty)
                        # Write the field according to price type field
                        product_obj.write(cr, uid, [product.id], {'standard_price': new_std_price})

                        # Record the values that were chosen in the wizard, so they can be
                        # used for inventory valuation if real-time valuation is enabled.
                        move_obj.write(cr, uid, [move.id],
                                {'price_unit': product_price,
                                 'price_currency_id': product_currency})


            for move in too_few:
                product_qty = move_product_qty[move.id]

                if not new_picking:
                    #POP-025
                    if pick.stock_journal_id and pick.stock_journal_id.sequence_id:
                        sequence_code = pick.stock_journal_id.sequence_id.code
                    else:
                        sequence_code = 'stock.picking.%s'%(pick.type)
                    new_picking = self.copy(cr, uid, pick.id,
                            {
                                'name': sequence_obj.get(cr, uid, sequence_code ),
                                'move_lines' : [],
                                'state':'draft',
                            })
                if product_qty != 0:
                    defaults = {
                            'product_qty' : product_qty,
                            'product_uos_qty': product_qty, #TODO: put correct uos_qty
                            'picking_id' : new_picking,
                            'state': 'waiting',
                            'move_dest_id': False,
                            'price_unit': move.price_unit,
                    }
                    prodlot_id = prodlot_ids[move.id]
                    if prodlot_id:
                        defaults.update(prodlot_id=prodlot_id)
                    move_obj.copy(cr, uid, move.id, defaults)

                move_obj.write(cr, uid, [move.id],
                        {
                            'product_qty' : move.product_qty - product_qty,
                            'product_uos_qty':move.product_qty - product_qty, #TODO: put correct uos_qty
                            'state': 'waiting',
                        })

            if new_picking:
                move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
            for move in complete:
                if prodlot_ids.get(move.id):
                    move_obj.write(cr, uid, move.id, {'prodlot_id': prodlot_ids[move.id]})
            for move in too_many:
                product_qty = move_product_qty[move.id]
                defaults = {
                    'product_qty' : product_qty,
                    'product_uos_qty': product_qty, #TODO: put correct uos_qty
                }
                prodlot_id = prodlot_ids.get(move.id)
                if prodlot_ids.get(move.id):
                    defaults.update(prodlot_id=prodlot_id)
                if new_picking:
                    defaults.update(picking_id=new_picking)
                move_obj.write(cr, uid, [move.id], defaults)


            # At first we confirm the new picking (if necessary)
            if new_picking:
                #wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
                # Then we finish the good picking
                self.write(cr, uid, [pick.id], {'backorder_id': new_picking})
                #self.action_move(cr, uid, [new_picking])
                #wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
                #wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
                delivered_pack_id = new_picking
            else:
                self.action_move(cr, uid, [pick.id])
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
                delivered_pack_id = pick.id

            delivered_pack = self.browse(cr, uid, delivered_pack_id, context=context)
            res[pick.id] = {'delivered_picking': delivered_pack.id or False}

        return res
    
#    def action_done(self, cr, uid, ids, context=None):
#        for pick in self.pool.get('stock.picking').browse(cr, uid, ids):
#            for sm in pick.move_lines:
#                product_id = sm.product_id.id
#                lot_id = sm.prodlot_id.id or False
#                location_src_id = sm.location_id.id 
#                location_dest_id = sm.location_dest_id.id
#                pack_id = sm.tracking_id.id or False
#                stock_report_obj = self.pool.get('ineco.stock.report')
#                source_ids = stock_report_obj.search(cr, uid, [('product_id','=',product_id),
#                    ('lot_id','=',lot_id),('location_dest_id','=',location_src_id),('tracking_id','=',pack_id)])
#                if source_ids:
#                    for line in self.pool.get('ineco.stock.report').browse(cr, uid, source_ids):
#                        line.write({'qty': line.available})
#                destination_ids = stock_report_obj.search(cr, uid, [('product_id','=',product_id),
#                    ('lot_id','=',lot_id),('location_dest_id','=',location_dest_id),('tracking_id','=',pack_id)])
#                if destination_ids:
#                    for line in self.pool.get('ineco.stock.report').browse(cr, uid, destination_ids):
#                        line.write({'qty': line.available})
#
#        return super(stock_picking, self).action_done(cr, uid, ids, context)

    #POP-008 Add new sequence by stock journal 
    def create(self, cr, user, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            if ('stock_journal_id' in vals) and (vals.get('stock_journal_id')):
                stock_journal = self.pool.get('stock.journal').browse(cr, user, [vals.get('stock_journal_id')])[0]
                if stock_journal:
                    seq_obj_name = stock_journal.sequence_id.code
                else:
                    seq_obj_name =  'stock.picking.' + vals['type']
            elif ('stock_journal_id' in context): #make stock_journal_id in context
                stock_journal_ids = self.pool.get('stock.journal').search(cr, user, [('name','=',context['stock_journal_id'])])
                if stock_journal_ids:
                    stock_journal = self.pool.get('stock.journal').browse(cr, user, stock_journal_ids)[0]
                    if stock_journal:
                        vals['stock_journal_id'] = stock_journal.id
                        seq_obj_name = stock_journal.sequence_id.code
                    else:
                        seq_obj_name =  'stock.picking.' + vals['type']
            else:
                seq_obj_name =  'stock.picking.' + vals['type']
            vals['name'] = self.pool.get('ir.sequence').get(cr, user, seq_obj_name)
        new_id = super(stock_picking, self).create(cr, user, vals, context)
        return new_id

    def action_done_draft(self, cr, uid, ids, *args):
        if not len(ids):
            return False
        cr.execute('select id from stock_move where picking_id in %s ', (tuple(ids),))
        move_ids = map(lambda x: x[0], cr.fetchall())
        #self.write(cr, uid, ids, {'state': 'confirmed'})
        #self.pool.get('stock.move').write(cr, uid, move_ids, {'state': 'confirmed'})
        #POP-015
        self.write(cr, uid, ids, {'state': 'draft'})
        self.pool.get('stock.move').write(cr, uid, move_ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for doc_id in ids:
            cr.execute("select id from wkf where osv = '"+'stock.picking'+"'")
            wkf_ids = map(lambda x: x[0], cr.fetchall())
            wkf_id = wkf_ids[0]
            cr.execute("select id from wkf_activity where wkf_id = %s and name = 'confirmed'",(str(wkf_id)))
            act_ids = map(lambda x: x[0], cr.fetchall())
            act_id = act_ids[0]
            cr.execute('update wkf_instance set state=%s where res_id=%s and res_type=%s', ('active', doc_id, 'stock.picking'))
            cr.execute("update wkf_workitem set state = 'active', act_id = %s where inst_id = (select id from wkf_instance where wkf_id = %s and res_id = %s)", (str(act_id), str(wkf_id), doc_id))
        
        for (id,name) in self.name_get(cr, uid, ids):
            message = _("The document '%s' has been set in confirm state.") % (name,)
            self.log(cr, uid, id, message)
        return True

    def action_cancel_draft(self, cr, uid, ids, *args):
        if not len(ids):
            return False
        cr.execute('select id from stock_move where picking_id in %s ', (tuple(ids),))
        move_ids = map(lambda x: x[0], cr.fetchall())
        #self.write(cr, uid, ids, {'state': 'confirmed'})
        #self.pool.get('stock.move').write(cr, uid, move_ids, {'state': 'confirmed'})
        #POP-015
        self.write(cr, uid, ids, {'state': 'draft'})
        self.pool.get('stock.move').write(cr, uid, move_ids, {'state': 'draft'})
        wf_service = netsvc.LocalService("workflow")
        for doc_id in ids:
            cr.execute("select id from wkf where osv = '"+'stock.picking'+"'")
            wkf_ids = map(lambda x: x[0], cr.fetchall())
            wkf_id = wkf_ids[0]
            cr.execute("select id from wkf_activity where wkf_id = %s and name = 'confirmed'",(str(wkf_id)))
            act_ids = map(lambda x: x[0], cr.fetchall())
            act_id = act_ids[0]
            cr.execute('update wkf_instance set state=%s where res_id=%s and res_type=%s', ('active', doc_id, 'stock.picking'))
            cr.execute("update wkf_workitem set state = 'active', act_id = %s where inst_id = (select id from wkf_instance where wkf_id = %s and res_id = %s)", (str(act_id), str(wkf_id), doc_id))
        
        for (id,name) in self.name_get(cr, uid, ids):
            message = _("The document '%s' has been set in confirm state.") % (name,)
            self.log(cr, uid, id, message)
        return True
    
    def schedule_check_available(self, cr, uid, context=None):
        #POP-005
        cr.execute("""
            select id from stock_picking
            where state in ('draft','confirmed','assigned') and type = 'out' and ineco_delivery_date is not null
            order by ineco_delivery_date, date_arrival
        """)
        dict1 = cr.dictfetchall()
        for row in dict1:
           pick_obj =  self.pool.get('stock.picking').browse(cr, uid, row['id'])
           pick_obj.action_assign()
    
    def schedule_check_location(self, cr, uid, context=None):
        cr.execute("""
            WITH RECURSIVE included_location(id, location_id) AS (
                SELECT id , location_id FROM stock_location WHERE 
                  id in (select lot_stock_id from stock_warehouse) or
                  id in (select lot_output_id from stock_warehouse) 
              UNION ALL
                SELECT p.id, p.location_id
                FROM included_location pr, stock_location p
                WHERE p.location_id = pr.id
              )
            select id, product_id from stock_move sm1
            where location_dest_id not in 
                (select sm2.location_id from stock_move sm2
                 where sm2.tracking_id = sm1.tracking_id and state <> 'cancel' )
              and tracking_id is not null
              and location_dest_id not in (
                SELECT id FROM stock_location
                WHERE id IN (SELECT id FROM included_location)
            ) and sm1.state <> 'cancel'       
        """)       
        move_dict = cr.dictfetchall()
        if move_dict:
            picking_id = False
            for move in move_dict:
                product_obj = self.pool.get('product.product').browse(cr, uid, [move['product_id']])[0]
                if product_obj:
                    if product_obj.keeping_id:
                        cr.execute("""
                            WITH RECURSIVE included_location(id, location_id) AS (
                                SELECT id , location_id FROM stock_location WHERE 
                                  id in (select lot_stock_id from stock_warehouse)
                              UNION ALL
                                SELECT p.id, p.location_id
                                FROM included_location pr, stock_location p
                                WHERE p.location_id = pr.id
                              )
                            select 
                              id,
                              name,
                              (select count(*) from stock_move where location_id = sl.id),
                              (select count(*) from stock_move where location_dest_id = sl.id)
                            from
                              stock_location sl
                            where 
                              (select count(*) from stock_move where location_id = sl.id and state <> 'cancel') - 
                              (select count(*) from stock_move where location_dest_id = sl.id and state <> 'cancel') = 0   
                              and id in (SELECT id FROM stock_location
                                     WHERE id IN (SELECT id FROM included_location)) 
                              and keeping_id = """ + str(product_obj.keeping_id.id) + """
                            order by name
                        """ )
                        location_availabel = cr.dictfetchall()
                        if location_availabel:
                            if not picking_id:
                                #create Internal Move Header
                                pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.internal')
                                picking_id = self.pool.get('stock.picking').create(cr, uid, {
                                    'name': pick_name,
                                    #'origin': order.name,
                                    'type': 'internal',
                                    'state': 'draft',
                                    'date': time.strftime('%Y-%m-%d'),
                    #                'move_type': order.picking_policy,
                                    'note': '',
                                    'invoice_state': 'none',
                     #               'company_id': order.company_id.id,
                                })
                                #                                
                            #print location_availabel[0]['name']
                            #create stock move for internal move
                            line = self.pool.get('stock.move').browse(cr, uid, [move['id']])[0]
                            move_id = self.pool.get('stock.move').create(cr, uid, {
                                'name': line.name[:64],
                                'picking_id': picking_id,
                                'product_id': line.product_id.id,
                                'date': time.strftime('%Y-%m-%d'),
                                'date_expected': time.strftime('%Y-%m-%d'),
                                'product_qty': line.product_qty,
                                'product_uom': line.product_uom.id,
                                'product_uos_qty': line.product_uos_qty,
                                'product_uos': (line.product_uos and line.product_uos.id)\
                                        or line.product_uom.id,
                                'product_packaging': line.product_packaging.id,
 #                               'address_id': line.address_allotment_id.id or order.partner_shipping_id.id,
                                'location_id': line.location_dest_id.id,
                                'location_dest_id': location_availabel[0]['id'],
 #                               'sale_line_id': line.id,
                                'tracking_id': line.tracking_id.id,
                                'prodlot_id': line.prodlot_id.id,
                                'state': 'draft',
                                'note': line.note,
#                                'company_id': order.company_id.id,
                            })
                            #

    #POP-007 Change Force Assigned
    def action_move(self, cr, uid, ids, context=None):
        """ Changes move state to assigned.
        @return: True
        """
        if context is None:
            context = {}

        user = self.pool.get('res.users').browse(cr, uid, uid)
        for pick in self.browse(cr, uid, ids, context=context):
            todo = []
            for move in pick.move_lines:
                if move.state in ['done','cancel']:
                    continue
                if user.company_id.skip_stock_report or pick.ineco_return:
                    if move.state == 'assigned':
                        todo.append(move.id)
                else:
                    #POP-014
                    #if pick.type in ['out','internal']:
                    if pick.type in ['internal']:
                        if move.location_id.validate_stock and pick.stock_journal_id.location_available :
                            lot_id = move.prodlot_id and move.prodlot_id.id or False
                            check_ids = self.pool.get('ineco.stock.report').search(cr, uid,
                                [('product_id','=',move.product_id.id),('location_dest_id','=',move.location_id.id), ('lot_id','=',lot_id),('qty','>',0)])
                            if check_ids:
                                stock_qty = 0
                                for stock in self.pool.get('ineco.stock.report').browse(cr, uid, check_ids): 
                                    stock_qty = stock_qty + stock.qty
                                #sql = """
                                #select ineco_get_stock(%s, %s) as total
                                #"""
                                #cr.execute(sql % (move.product_uom.id, str(int(move.product_qty))))
                                #total = cr.dictfetchall()
                                total = self.pool.get('product.uom')._compute_qty(cr, uid, move.product_uom, move.product_qty, context.get('uom', False))                                
                                product_qty = 0
                                if total:
                                    #product_qty = total[0]['total']
                                    product_qty = total
                                    if stock_qty >= product_qty: #change in default_uom qty 
                                        if move.state == 'assigned':
                                            todo.append(move.id)
                                    else:
                                        raise osv.except_osv(_('Error !'), _('Stock insufficient in source location. [' + move.product_id.name+ ' (Need:'+ str(move.product_qty) + ') ' + '->'+
                                                                             move.location_id.name+ ' (Available:'+ str(stock_qty) + ') ]'))
                            else:
                                raise osv.except_osv(_('Error !'), _('Can not found "'+move.product_id.name+'" in '+move.location_id.name+'. Please checking Stock Report.'))
                        else:
                            #Location Not Validate Stock
                            todo.append(move.id)
                    else:
                        if move.state == 'assigned':
                            todo.append(move.id)
            if len(todo):
                self.pool.get('stock.move').action_done(cr, uid, todo, context=context)
                for sm in self.pool.get('stock.move').browse(cr, uid, todo, context=context):
                    product_id = sm.product_id.id
                    lot_id = sm.prodlot_id.id or False
                    location_src_id = sm.location_id.id 
                    location_dest_id = sm.location_dest_id.id
                    pack_id = sm.tracking_id.id or False
                    stock_report_obj = self.pool.get('ineco.stock.report')
                    source_ids = stock_report_obj.search(cr, uid, [('product_id','=',product_id),
                        ('lot_id','=',lot_id),('location_dest_id','=',location_src_id),('tracking_id','=',pack_id)])
                    if source_ids:
                        for line in self.pool.get('ineco.stock.report').browse(cr, uid, source_ids):
                            line.write({'qty': line.available})
                    destination_ids = stock_report_obj.search(cr, uid, [('product_id','=',product_id),
                        ('lot_id','=',lot_id),('location_dest_id','=',location_dest_id),('tracking_id','=',pack_id)])
                    if destination_ids:
                        for line in self.pool.get('ineco.stock.report').browse(cr, uid, destination_ids):
                            line.write({'qty': line.available})
        return True

    def action_assign(self, cr, uid, ids, *args):
        """ Changes state of picking to available if all moves are confirmed.
        @return: True
        """
        for pick in self.browse(cr, uid, ids):
            if pick.type in ['out','internal']:             
                move_ids = [x.id for x in pick.move_lines if x.state == 'confirmed']
                #if not move_ids:
                #    raise osv.except_osv(_('Warning !'),_('Not enough stock, unable to reserve the products.'))
                if move_ids:
                    self.pool.get('stock.move').action_assign(cr, uid, move_ids)
            else:
                for move in pick.move_lines:
                    move.write({'state':'assigned'})
                pick.write({'state':'assigned'})
        return True
    
stock_picking()

class ineco_production_lot_lastmove(osv.osv):
    _name = 'ineco.production.lot.lastmove'
    _description = 'View stock move last location only'
    _auto = False
    _columns = {
        'name': fields.char('Name', size=62),
        'date_expected': fields.datetime('Date Expected'),
        'date': fields.datetime('Date'),
        'prodlot_id': fields.many2one('stock.production.lot', 'Production Lot'),
        'tracking_id': fields.many2one('stock.tracking','Pack'),
        'product_qty': fields.float('Qty'),
        'product_uom': fields.many2one('product.uom', 'UOM'),
        'location_id': fields.many2one('stock.location', 'From Location'),
        'location_dest_id': fields.many2one('stock.location', 'Last Location'),
        'product_id': fields.many2one('product.product', 'Product'),
        'picking_id': fields.many2one('stock.picking','Picking'),
        'state': fields.char('State', size=24)
    }
    
    _order = "date"
    
    def init(self, cr):
        cr.execute("""
            create or replace view ineco_production_lot_lastmove as (
            select 
              sm.id,
              sm.name,  
              sm.date_expected,
              sm.date,
              sm.prodlot_id,
              sm.tracking_id,
              sm.product_qty,
              sm.product_uom,
              sm.location_id,
              sm.location_dest_id,
              sm.product_id,
              sm.picking_id,
              sm.state   
            from 
              stock_move sm
            left join stock_production_lot spl on sm.prodlot_id = spl.id
            where 
              sm.id in 
                (select id from stock_move sm2 where sm.tracking_id = sm2.tracking_id 
                 order by date desc limit 1)    
            )    
        """)
        
ineco_production_lot_lastmove()


class stock_production_lot(osv.osv):
    
    _name = "stock.production.lot"
    _inherit = "stock.production.lot"
    _description = "Add Expiry Date in Production Lot"

    #POP-019
    #    update stock_production_lot
    #    set name = name || '-' || ltrim(to_char(id,'9999999'))
    #    where id in (
    #    select id from stock_production_lot
    #    where name in (
    #    select name from stock_production_lot
    #    group by name
    #    having count(*) > 1) )
    #
    #_sql_constraints = [
    #    ('name_unique_idx', 'unique (name)', 'Production Lot Must be unique !')
    #]

    def _get_expire_context(self, cr, uid, context=None):
        result = False
        if 'wip_expired_date' in context:
            result = context['wip_expired_date']
        else:
            result = (datetime.today() + relativedelta( years = 1)).strftime('%Y-%m-%d')
        return result

    #POP-027
    def _get_stock(self, cr, uid, ids, field_name, arg, context=None):
        """ Gets stock of products for locations
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        if 'location_id' not in context:
            stock_ids = self.pool.get('stock.location').search(cr, uid, [('name','=','Stock')])
            locations = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal'),('location_id','child_of',stock_ids)], context=context)
        else:
            locations = context['location_id'] and [context['location_id']] or []

        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}.fromkeys(ids, 0.0)
        if locations:
            cr.execute('''select
                    prodlot_id,
                    round(sum(qty),4)
                from
                    stock_report_prodlots
                where
                    location_id IN %s and prodlot_id IN %s group by prodlot_id ''',(tuple(locations),tuple(ids),))
            #cr.execute('''select
            #        lot_id,
            #        sum(ineco_get_stock(uom_id,qty))
            #    from
            #        ineco_stock_report_master
            #    where
            #        location_dest_id IN %s and lot_id IN %s group by lot_id''',(tuple(locations),tuple(ids),))
            res.update(dict(cr.fetchall()))

        return res

    #POP-027
    def _stock_search(self, cr, uid, obj, name, args, context=None):
        """ Searches Ids of products
        @return: Ids of locations
        """
        stock_ids = self.pool.get('stock.location').search(cr, uid, [('name','=','Stock')])
        locations = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal'),('location_id','child_of',stock_ids)], context=context)
        #locations = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')])
        cr.execute('''select
                prodlot_id,
                round(sum(qty),4)
            from
                stock_report_prodlots
            where
                location_id IN %s group by prodlot_id
            having  round(sum(qty),4) '''+ str(args[0][1]) + str(args[0][2]),(tuple(locations),))
        res = cr.fetchall()
        ids = [('id', 'in', map(lambda x: x[0], res))]
        return ids
    
    _columns = {
        'stock_available': fields.function(_get_stock, fnct_search=_stock_search, method=True, type="float", string="Available", select=True,
            help="Current quantity of products with this Production Lot Number available in company warehouses",
            digits_compute=dp.get_precision('Product UoM')),
        "date_expired": fields.date('Expire Date', help="Date of Expiration"),
        "lastmove_ids": fields.one2many('ineco.production.lot.lastmove', 'prodlot_id', 'Last Move'),
        'stock_report_ids': fields.one2many('ineco.stock.report','lot_id','Stock Report'),
        'ineco_mfg_printed': fields.char('MFG Printed', size=50),
        
    }
    
    _defaults = {
        #"date_expired": time.strftime('%Y-%m-%d')
        'date_expired': _get_expire_context ,
    }
    
    _order = 'date_expired, name'
    
stock_production_lot()

class stock_move_split_lines(osv.osv_memory):
    _name = "stock.move.split.lines"
    _inherit = "stock.move.split.lines"
    _description = "Add Default LOT Name in Split lines"
    
    _defaults = {
        'name': '/',
        'quantity': 0 
        #lambda x, y, z, c: x.pool.get('ir.sequence').get(y, z, 'stock.lot.serial'),
    }

    def create(self, cr, user, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            sequence_id = self.pool.get('ir.sequence').get(cr, user, 'stock.lot.serial')
            if not sequence_id:                
                raise osv.except_osv(_('Error !'), _('Can not find Lot Sequence for Company.'))                
            vals['name'] = sequence_id
        if 'quantity' in vals:
            quantity = vals.get('quantity') or 0.0
            if quantity == 0:
                active_id = context.get('active_id')
                move_obj = self.pool.get('stock.move').browse(cr, user, [active_id])[0]
                vals['quantity'] = move_obj.product_qty
            
        return super(stock_move_split_lines,self).create(cr, user, vals, context)
        
stock_move_split_lines()

class split_in_production_lot(osv.osv_memory):
    
    _name = "stock.move.split"
    _inherit = "stock.move.split"
    _description = "Split in Production lots"
 
    def split(self, cr, uid, ids, move_ids, context=None):
        """ To split stock moves into production lot
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: the ID or list of IDs if we want more than one
        @param move_ids: the ID or list of IDs of stock move we want to split
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        inventory_id = context.get('inventory_id', False)
        prodlot_obj = self.pool.get('stock.production.lot')
        inventory_obj = self.pool.get('stock.inventory')
        move_obj = self.pool.get('stock.move')
        new_move = []
        for data in self.browse(cr, uid, ids, context=context):
            for move in move_obj.browse(cr, uid, move_ids, context=context):
                move_qty = move.product_qty
                quantity_rest = move.product_qty
                uos_qty_rest = move.product_uos_qty
                new_move = []
                if data.use_exist:
                    lines = [l for l in data.line_exist_ids if l]
                else:
                    lines = [l for l in data.line_ids if l]
                
                for line in lines:
                    if len(lines) == 0:
                        if line.quantity == 0:
                            quantity = move.product_qty
                        else:
                            quantity = line.quantity
                    else:
                        quantity = line.quantity
                    if quantity <= 0 or move_qty == 0:
                        continue
                    quantity_rest -= quantity
                    uos_qty = quantity / move_qty * move.product_uos_qty
                    uos_qty_rest = quantity_rest / move_qty * move.product_uos_qty
                    if quantity_rest < 0:
                        quantity_rest = quantity
                        break
                    default_val = {
                        'product_qty': quantity,
                        'product_uos_qty': uos_qty,
                        'state': move.state
                    }
                    if quantity_rest > 0:
                        current_move = move_obj.copy(cr, uid, move.id, default_val, context=context)
                        if inventory_id and current_move:
                            inventory_obj.write(cr, uid, inventory_id, {'move_ids': [(4, current_move)]}, context=context)
                        new_move.append(current_move)

                    if quantity_rest == 0:
                        current_move = move.id
                    prodlot_id = False
                    if data.use_exist:
                        prodlot_id = line.prodlot_id.id
                    if not prodlot_id:
                        prodlot_id = prodlot_obj.create(cr, uid, {
                            'name': line.name,
                            'product_id': move.product_id.id},
                        context=context)

                    move_obj.write(cr, uid, [current_move], {'prodlot_id': prodlot_id, 'state':move.state})

                    update_val = {}
                    if quantity_rest > 0:
                        update_val['product_qty'] = quantity_rest
                        update_val['product_uos_qty'] = uos_qty_rest
                        update_val['state'] = move.state
                        move_obj.write(cr, uid, [move.id], update_val)

        return new_move
    
split_in_production_lot()

#POP-011 MOVE -> Product.py
#class ineco_stock_keeping_method(osv.osv):
#    
#    def _get_location_count(self, cr, uid, ids, field_name, arg, context={}):
#        res = {}
#        sql = "select count(*) as total from stock_location where keeping_id = %s"
#        for each in ids:
#            cr.execute(sql % (each))
#            count =  cr.dictfetchall()
#            res[each] = count[0]['total']
#        return res

#    def _get_location_available(self, cr, uid, ids, field_name, arg, context={}):
#        res = {}
#        sql = """ 
#                select 
#                  iskm.id,
#                  (select count(*) from stock_location where stock_location.keeping_id = iskm.id) as total,
#                  sum(case abs( (select count(*) from stock_move sm1 where sm1.location_dest_id = sl.id) -
#                    (select count(*) from stock_move sm1 where sm1.location_id = sl.id) )
#                    when 0 then 0
#                    else 1 
#                  end) as already,
#                  (select count(*) from stock_location where stock_location.keeping_id = iskm.id) - 
#                  sum(case abs( (select count(*) from stock_move sm1 where sm1.location_dest_id = sl.id) -
#                    (select count(*) from stock_move sm1 where sm1.location_id = sl.id) )
#                    when 0 then 0
#                    else 1 
#                  end) as available
#                from
#                  ineco_stock_keeping_method iskm
#                left join stock_location sl on iskm.id = sl.keeping_id
#                where iskm.id = %s
#                group by iskm.id, total
#        """
#        for each in ids:
#            cr.execute(sql % (each))
#            count =  cr.dictfetchall()
#            res[each] = count[0]['available']
#        return res
    
#    _name = "ineco.stock.keeping.method"
#    _description = "Method for keeping wizard location."
#    _columns = {
#        'name': fields.char('Name', size=128, required=True),
#        'total_location': fields.function(_get_location_count, string="Location Count", type="integer", method=True),
#        'available_location': fields.function(_get_location_available, string="Available", type="integer", method=True),
#        'location_ids': fields.one2many('stock.location','keeping_id','Locations'),
#        'active': fields.boolean('Active')
#    }
#    _defaults = {
#        'active': True
#    }
#ineco_stock_keeping_method()

class stock_location(osv.osv):
    
    def _get_location_available(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        sql = """
                select 
                  case abs( (select count(*) from stock_move sm1 where sm1.location_dest_id = sl.id) -
                  (select count(*) from stock_move sm1 where sm1.location_id = sl.id) )
                    when 0 then 0
                    else 1
                  end as available
                from 
                  stock_location sl
                where 
                  sl.id = %s        
        """    
        for each in ids:
            cr.execute(sql % (each))
            count =  cr.dictfetchall()
            res[each] = count[0]['available']
        return res

    def _product_value(self, cr, uid, ids, field_names, arg, context=None):
        """Computes stock value (real and virtual) for a product, as well as stock qty (real and virtual).
        @param field_names: Name of field
        @return: Dictionary of values
        """
        prod_id = context and context.get('product_id', False)

        product_product_obj = self.pool.get('product.product')

        cr.execute('select distinct product_id, location_id from stock_move where location_id in %s', (tuple(ids), ))
        dict1 = cr.dictfetchall()
        cr.execute('select distinct product_id, location_dest_id as location_id from stock_move where location_dest_id in %s', (tuple(ids), ))
        dict2 = cr.dictfetchall()
        res_products_by_location = sorted(dict1+dict2, key=itemgetter('location_id'))
        products_by_location = dict((k, [v['product_id'] for v in itr]) for k, itr in groupby(res_products_by_location, itemgetter('location_id')))

        result = dict([(i, {}.fromkeys(field_names, 0.0)) for i in ids])
        result.update(dict([(i, {}.fromkeys(field_names, 0.0)) for i in list(set([aaa['location_id'] for aaa in res_products_by_location]))]))

        currency_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.currency_id.id
        currency_obj = self.pool.get('res.currency')
        currency = currency_obj.browse(cr, uid, currency_id, context=context)
        for loc_id, product_ids in products_by_location.items():
            if prod_id:
                product_ids = [prod_id]
            c = (context or {}).copy()
            c['location'] = loc_id
            for prod in product_product_obj.browse(cr, uid, product_ids, context=c):
                for f in field_names:
                    if f == 'ineco_stock_real':
                        if loc_id not in result:
                            result[loc_id] = {}
                        result[loc_id][f] += prod.qty_available
                    elif f == 'stock_virtual':
                        result[loc_id][f] += prod.virtual_available
                    elif f == 'stock_real_value':
                        amount = prod.qty_available * prod.standard_price
                        amount = currency_obj.round(cr, uid, currency, amount)
                        result[loc_id][f] += amount
                    elif f == 'stock_virtual_value':
                        amount = prod.virtual_available * prod.standard_price
                        amount = currency_obj.round(cr, uid, currency, amount)
                        result[loc_id][f] += amount
        return result
    
    
    _name = "stock.location"
    _inherit = "stock.location"
    _description = "Add Keeping Method"
    _columns = {
        'keeping_id': fields.many2one('ineco.stock.keeping.method', 'Keeping Method', ondelete="restrict"),
        'available': fields.function(_get_location_available, string="Available", type="boolean", method=True),
        'validate_stock': fields.boolean('Validate Stock')
#        'ineco_stock_real': fields.function(_product_value, store=True, method=True, type='float', string='Real Stock', multi="stock"),
    }
    
    _defaults = {
        'validate_stock': False,
    }
    
stock_location()

class ineco_stock_kitting_draft(osv.osv):
    _name = 'ineco.stock.kitting.draft'
    _description = 'Draft view for Kitting Draft'
    _auto = False
    _columns = {
        'product_id': fields.many2one('product.product','Product'),
        'prodlot_id': fields.many2one('stock.production.lot', 'Production Lot'),
        'tracking_id': fields.many2one('stock.tracking', 'Pack'),
        'date_expected': fields.datetime('Date Expected', 'Delivery Date'),
        'location_id': fields.many2one('stock.location', 'Location'),
    }
    
    def init(self, cr):
        cr.execute("""
            create or replace view ineco_stock_kitting_draft as
            select distinct 
              sm.prodlot_id,
              sm.tracking_id,
              sp.ineco_delivery_date::timestamp as date_expected,
              coalesce(sm.location_id,0) as location_id,
              pp.id as product_id
            from stock_move sm
            left join stock_picking sp on sm.picking_id = sp.id 
            left join product_product pp on sm.product_id = pp.id
            where 
              sp.type = 'out' and
              sm.state not in ('cancel') and (sm.prodlot_id is not null or sm.tracking_id is not null)      
        """)
    
ineco_stock_kitting_draft()

class ineco_stock_kitting(osv.osv):
    _name = 'ineco.stock.kitting'
    _description = 'Draft view for Kitting'
    _auto = False
    _columns = {
        'product_id': fields.many2one('product.product', 'Product'),
        'prodlot_id': fields.many2one('stock.production.lot', 'Production Lot'),
        'tracking_id': fields.many2one('stock.tracking', 'Pack'),
        'date_expected': fields.datetime('Date Expected', 'Delivery Date'),
        'location_id': fields.many2one('stock.location', 'Location'),
    }
    _order = "product_id, prodlot_id, tracking_id, location_id"
    
    def init(self, cr):
        cr.execute("""
            create or replace view ineco_stock_kitting as 
            select id, (a[id]).* from (
            select a, generate_series(1, array_upper(a,1)) as id from (
            select array (
              select ineco_stock_kitting_draft from ineco_stock_kitting_draft
            ) as a ) b ) c        
        """)
    
ineco_stock_kitting()

class stock_tracking(osv.osv):
    
    _name = "stock.tracking"
    _inherit = "stock.tracking"
    _description = "Reset Tracking ID"

    def _get_stock(self, cr, uid, ids, field_name, arg, context=None):
        """ Gets stock of products for locations
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        tracking = self.pool.get('stock.tracking').search(cr, uid, [], context=context)

        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}.fromkeys(ids, 0.0)
        if tracking:
            cr.execute('''select
                    tracking_id,
                    sum(ineco_get_stock(uom_id,qty))
                from
                    ineco_stock_report_master
                where
                    tracking_id IN %s group by tracking_id''',(tuple(tracking),))
            res.update(dict(cr.fetchall()))

        return res

    _columns = {
        'stock_available': fields.function(_get_stock, method=True, type="float", string="Available",
            help="Current quantity of products with this Pack No available in company warehouses",
            digits_compute=dp.get_precision('Product UoM')),
##        'track_line_ids': fields.one2many('ineco.stock.tracking.line','tracking_id','History'),
        'product_id': fields.many2one('product.product','Product'),
    }

    # update stock_tracking
    # set name = name || '-' || ltrim(to_char(id,'9999999'))
    # where id in (
    # select id from stock_tracking
    # where name in (
    # select name from stock_tracking
    # group by name
    # having count(*) > 1) )
    
    # create index ineco_stock_report_master_tracking_idx on ineco_stock_report_master (tracking_id)

    _sql_constraints = [
        ('name_product_unique_idx', 'unique (name, product_id)', 'Pack No and Product must be unique !')
    ]
    
    def make_id(self, cr, uid, context=None):
        sequence = self.pool.get('ir.sequence').get(cr, uid, 'stock.lot.tracking')
        return sequence
        
    _defaults = {
        'name': make_id
    }

stock_tracking()

#POP-004
class ineco_stock_tracking_line(osv.osv):
    _name = "ineco.stock.tracking.line"
    _description = "Stock Tracking Line"
    _columns = {
        'name': fields.char('Description', size=30),
        'move_id': fields.many2one('stock.move','Move'),
        'tracking_id': fields.many2one('stock.tracking','Pack'),
    }
ineco_stock_tracking_line()

#POP-001
class ineco_stock_report_draft_one(osv.osv):
    _name = 'ineco.stock.report.draft.one'
    _description = 'Stock Draft Query Report'
    _auto = False
    
    def init(self,cr):
        cr.execute("""
            create or replace view ineco_stock_report_draft_one as 
                       WITH RECURSIVE included_location(id, location_id) AS (
                           SELECT id , location_id FROM stock_location WHERE 
                              id in (select lot_stock_id from stock_warehouse)
                           UNION ALL
                              SELECT p.id, p.location_id
                              FROM included_location pr, stock_location p
                              WHERE p.location_id = pr.id
                        )
            select
              id, prodlot_id, tracking_id, product_id, location_id, location_dest_id, product_uom, product_qty, date
            from
              stock_move 
            where 
              tracking_id not in (
              select 
                tracking_id
              from stock_move
              where location_id in (select id from included_location) and location_dest_id not in (select id from included_location)
            ) and stock_move.state <> 'cancel'
        """)
        
ineco_stock_report_draft_one()
    
class ineco_stock_report_draft(osv.osv):
    
    _name = 'ineco.stock.report.draft'
    _description = 'Stock Reporting'
    _auto = False
    
    def init(self, cr):
        cr.execute("""
            create or replace view ineco_stock_report_draft as
            select 
              stock_location.id as location_dest_id,
              ineco_stock_report_draft_one.prodlot_id as lot_id,
              stock_production_lot.date_expired as expired,
              ineco_stock_report_draft_one.tracking_id,
              ineco_stock_report_draft_one.product_id,
              ineco_stock_report_draft_one.product_uom as uom_id,
              sum(ineco_stock_report_draft_one.product_qty) as qty
            from
              stock_location
            left join ineco_stock_report_draft_one on stock_location.id = ineco_stock_report_draft_one.location_dest_id
            left join stock_production_lot on ineco_stock_report_draft_one.prodlot_id = stock_production_lot.id
            where
              stock_location.id not in (select ineco_stock_report_draft_one.location_id from ineco_stock_report_draft_one)
            group by
              stock_location.id ,
              ineco_stock_report_draft_one.prodlot_id,
              stock_production_lot.date_expired,
              ineco_stock_report_draft_one.tracking_id,
              ineco_stock_report_draft_one.product_id,
              ineco_stock_report_draft_one.product_uom
        """)
    
ineco_stock_report_draft()

#POP-002
class ineco_stock_report_template_a(osv.osv):
    _name = 'ineco.stock.report.template.a'
    _description = 'Stock Report Template A'
    _auto = False

#            select product_id, product_uom, prodlot_id, tracking_id, location_dest_id as location_id, sum(product_qty) as qty
#            from stock_move 
#            where location_id NOT IN (select id from included_location)
#            and location_dest_id IN (select id from included_location)
#            and state IN ('done')
#            group by product_id,product_uom, prodlot_id, tracking_id, location_dest_id
#            union
#            select product_id, product_uom, prodlot_id, tracking_id, location_dest_id as location_id, sum(product_qty) as qty
#            from stock_move 
#            where location_id IN (select id from included_location)
#            and location_dest_id IN (select id from included_location)
#            and state IN ('done')
#            group by product_id,product_uom, prodlot_id, tracking_id, location_dest_id
#            union
#            select product_id, product_uom, prodlot_id, tracking_id, location_id as location_id, -sum(product_qty) as qty
#            from stock_move 
#            where location_id IN (select id from included_location)
#            and location_dest_id NOT IN (select id from included_location)
#            and state IN ('done')
#            group by product_id,product_uom, prodlot_id, tracking_id, location_id
#            union
#            select product_id, product_uom, prodlot_id, tracking_id, location_id as location_id, -sum(product_qty) as qty
#            from stock_move 
#            where location_id IN (select id from included_location)
#            and location_dest_id IN (select id from included_location)
#            and state IN ('done')
#            group by product_id,product_uom, prodlot_id, tracking_id, location_id
#            order by location_id
    
    def init(self,cr):
        cr.execute("""
            create or replace view ineco_stock_report_template_a as
               WITH RECURSIVE included_location(id, location_id) AS (
                   SELECT id , location_id FROM stock_location WHERE 
                      id in (select lot_stock_id from stock_warehouse)
                   UNION ALL
                      SELECT p.id, p.location_id
                      FROM included_location pr, stock_location p
                      WHERE p.location_id = pr.id
                )

            select product_id, uom_id as product_uom, prodlot_id, tracking_id, location_dest_id as location_id, sum(ineco_get_stock(product_uom,product_qty))::decimal as qty
            from stock_move 
            join product_template on stock_move.product_id = product_template.id
            where location_id NOT IN (select id from included_location)
            and location_dest_id IN (select id from included_location)
            and stock_move.state IN ('done')
            group by product_id,uom_id, prodlot_id, tracking_id, location_dest_id
            
            union
            select product_id, uom_id as product_uom, prodlot_id, tracking_id, location_dest_id as location_id, sum(ineco_get_stock(product_uom,product_qty))::decimal as qty
            from stock_move 
            join product_template on stock_move.product_id = product_template.id
            where location_id IN (select id from included_location)
            and location_dest_id IN (select id from included_location)
            and stock_move.state IN ('done')
            group by product_id,uom_id, prodlot_id, tracking_id, location_dest_id
            
            union
            select product_id, uom_id as product_uom, prodlot_id, tracking_id, location_id as location_id, -sum(ineco_get_stock(product_uom,product_qty))::decimal as qty
            from stock_move 
            join product_template on stock_move.product_id = product_template.id            
            where location_id IN (select id from included_location)
            and location_dest_id NOT IN (select id from included_location)
            and stock_move.state IN ('done')
            group by product_id,uom_id, prodlot_id, tracking_id, location_id
            
            union
            select product_id, uom_id as product_uom, prodlot_id, tracking_id, location_id as location_id, -sum(ineco_get_stock(product_uom,product_qty))::decimal as qty
            from stock_move 
            join product_template on stock_move.product_id = product_template.id            
            where location_id IN (select id from included_location)
            and location_dest_id IN (select id from included_location)
            and stock_move.state IN ('done')
            group by product_id,uom_id, prodlot_id, tracking_id, location_id
            order by location_id

        """)
        
ineco_stock_report_template_a()    

class ineco_stock_report_template_b(osv.osv):
    _name = 'ineco.stock.report.template.b'
    _description = 'Stock Report Template B'
    _auto = False

    #POP-005    
    def init(self,cr):
        cr.execute("""
            create or replace view ineco_stock_report_template_b as
            select 
              ineco_stock_report_template_a.location_id as location_id,
              prodlot_id,
              stock_production_lot.date_expired as expired,
              tracking_id,
              ineco_stock_report_template_a.product_id as product_id, 
              product_uom,
              sum(qty) as qty,
              stock_production_lot.date as date_input
            from ineco_stock_report_template_a
            left join stock_production_lot on ineco_stock_report_template_a.prodlot_id = stock_production_lot.id
            group by ineco_stock_report_template_a.location_id, prodlot_id, stock_production_lot.date_expired, stock_production_lot.date, tracking_id, ineco_stock_report_template_a.product_id, product_uom
            having sum(qty) <> 0
            order by location_id
        """)
        
ineco_stock_report_template_b()

class ineco_stock_report_template_c(osv.osv):
    _name = 'ineco.stock.report.template.c'
    _description = 'Stock Report Template C'
    _auto = False
    
    #POP-005
    def init(self,cr):
        cr.execute("""
            create or replace view ineco_stock_report_template_c as
               WITH RECURSIVE included_location(id, location_id) AS (
                   SELECT id , location_id FROM stock_location WHERE 
                      id in (select lot_stock_id from stock_warehouse)
                   UNION ALL
                      SELECT p.id, p.location_id
                      FROM included_location pr, stock_location p
                      WHERE p.location_id = pr.id
                )
            select
              stock_location.id as location_dest_id,
              prodlot_id as lot_id,
              expired,
              tracking_id,
              product_id,
              product_uom as uom_id,
              qty,
              product_product.warehouse_uom,
              ineco_convert_stock(product_product.warehouse_uom, qty) as warehouse_qty,
              date_input
            from 
              stock_location 
            left join  ineco_stock_report_template_b on stock_location.id = ineco_stock_report_template_b.location_id
            left join  product_product on product_id = product_product.id
            where stock_location.id in (select id from included_location )
        """)
        
ineco_stock_report_template_c()

class ineco_stock_report_template_d(osv.osv):
    _name = 'ineco.stock.report.template.d'
    _description = 'Stock Report Template D'
    _auto = False

    def drop_table_if_exists(cr, tablename):
        cr.execute("select count(1) from pg_class where relkind=%s and relname=%s", ('r', tablename,))
        if cr.fetchone()[0]:
            cr.execute("DROP table %s" % (tablename,))
            cr.commit()
        return True
    
    def init(self, cr):
        #tools.sql.drop_view_if_exists(cr, 'tmp_ineco_stock_report')
        cr.execute("""
            create or replace view tmp_ineco_stock_report as (
                select id, (a[id]).*
                from (
                    select a, generate_series(1, array_upper(a,1)) as id
                        from (
                            select array (
                                select ineco_stock_report_template_c from ineco_stock_report_template_c

                            ) as a
                    ) b
                ) c        
            )
        """)
        #tools.sql.drop_view_if_exists(cr, 'ineco_stock_report')
        #cr.execute("select count(1) from pg_class where relkind=%s and relname=%s", ('r', 'ineco_stock_report'))
        #if cr.fetchone()[0]:
        #    cr.execute("DROP table %s" % ('ineco_stock_report'))
        #    cr.commit()

        #cr.execute("select * into ineco_stock_report from tmp_ineco_stock_report")

ineco_stock_report_template_d()

class ineco_stock_report(osv.osv):

    def _get_product_available(self, cr, uid, ids, field_name, arg, context=None):
        """ Finds whether product is available or not in particular warehouse.
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        context.update({ 'states': ('done',), 'what': ('in', 'out') })
        states = context.get('states',[])
        what = context.get('what',())
        if not ids:
            ids = self.search(cr, uid, [])
        res = {}.fromkeys(ids, 0.0)
        if not ids:
            return res
        
        for line in self.browse(cr, uid, ids):

            # TODO: write in more ORM way, less queries, more pg84 magic
            if line.product_id:            
                if context.get('shop', False):
                    cr.execute('select warehouse_id from sale_shop where id=%s', (int(context['shop']),))
                    res2 = cr.fetchone()
                    if res2:
                        context['warehouse'] = res2[0]
        
                if context.get('warehouse', False):
                    cr.execute('select lot_stock_id from stock_warehouse where id=%s', (int(context['warehouse']),))
                    res2 = cr.fetchone()
                    if res2:
                        context['location'] = res2[0]
        
                #if context.get('location', False):
                #    if type(context['location']) == type(1):
                #        location_ids = [context['location']]
                #    elif type(context['location']) in (type(''), type(u'')):
                #        location_ids = self.pool.get('stock.location').search(cr, uid, [('name','ilike',context['location'])], context=context)
                #    else:
                #        location_ids = context['location']
                #else:
                #    location_ids = []
                #    wids = self.pool.get('stock.warehouse').search(cr, uid, [], context=context)
                #    for w in self.pool.get('stock.warehouse').browse(cr, uid, wids, context=context):
                #        location_ids.append(w.lot_stock_id.id)
        
                location_ids = [line.location_dest_id.id]
    
                # build the list of ids of children of the location given by id
                #if context.get('compute_child',True):
                #    child_location_ids = self.pool.get('stock.location').search(cr, uid, [('location_id', 'child_of', location_ids)])
                #    location_ids = child_location_ids or location_ids
                #else:
                #    location_ids = location_ids
        
                uoms_o = {}
                product2uom = {}
                for product in self.pool.get('product.template').browse(cr, uid, [line.product_id.id], context=context):
                    try:                                         
                        product2uom[product.id] = product.uom_id.id
                        uoms_o[product.uom_id.id] = product.uom_id
                    except:
                        pass
        
                results = []
                results2 = []
        
                #from_date = context.get('from_date',False)
                #to_date = context.get('to_date',False)
                #date_str = False
                #date_values = False
                where = [tuple(location_ids),tuple(location_ids),tuple([line.product_id.id]),tuple(states)]
                #if from_date and to_date:
                #    date_str = "date>=%s and date<=%s"
                #    where.append(tuple([from_date]))
                #    where.append(tuple([to_date]))
                #elif from_date:
                #    date_str = "date>=%s"
                #    date_values = [from_date]
                #elif to_date:
                #    date_str = "date<=%s"
                #    date_values = [to_date]
        
        
                # TODO: perhaps merge in one query.
                #if date_values:
                #    where.append(tuple(date_values))
                prodlot_sql = ''
                if line.lot_id:
                    prodlot_sql = ' = '+str(line.lot_id.id)
                else:
                    prodlot_sql = ' is null '
                tracking_sql = ''
                if line.tracking_id:
                    tracking_sql = ' = '+str(line.tracking_id.id)
                else:
                    tracking_sql = ' is null '
                if 'in' in what:
                    # all moves from a location out of the set to a location in the set
                    cr.execute(
                        'select sum(product_qty), product_id, product_uom '\
                        'from stock_move '\
                        'where location_id NOT IN %s'\
                        'and location_dest_id IN %s'\
                        'and product_id IN %s'\
                        'and state IN %s' + ' '\
                        'and prodlot_id ' + prodlot_sql + ' '\
                        'and tracking_id ' + tracking_sql+ ' '\
                        'group by product_id,product_uom',tuple(where))
                    results = cr.fetchall()
                if 'out' in what:
                    # all moves from a location in the set to a location out of the set
                    cr.execute(
                        'select sum(product_qty), product_id, product_uom '\
                        'from stock_move '\
                        'where location_id IN %s'\
                        'and location_dest_id NOT IN %s '\
                        'and product_id  IN %s'\
                        'and state in %s' + ' '\
                        'and prodlot_id ' + prodlot_sql + ' '\
                        'and tracking_id ' + tracking_sql+ ' '\
                        'group by product_id,product_uom',tuple(where))
                    results2 = cr.fetchall()
                uom_obj = self.pool.get('product.uom')
                uoms = map(lambda x: x[2], results) + map(lambda x: x[2], results2)
                if context.get('uom', False):
                    uoms += [context['uom']]
        
                uoms = filter(lambda x: x not in uoms_o.keys(), uoms)
                if uoms:
                    uoms = uom_obj.browse(cr, uid, list(set(uoms)), context=context)
                    for o in uoms:
                        uoms_o[o.id] = o
                #TOCHECK: before change uom of product, stock move line are in old uom.
                context.update({'raise-exception': False})
                for amount, prod_id, prod_uom in results:
                    try:
                        amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
                                 uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
                    except:
                        amount = 0
                    res[line.id] += amount
                for amount, prod_id, prod_uom in results2:
                    try:
                        amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
                                uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
                    except:
                        amount = 0
                    res[line.id] -= amount
        return res

    #POP-021
    def _problemed(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.qty <> line.available
        return res

    def _problemed_search(self, cr, uid, obj, name, args, context=None):
        res = {}
        sql = """
            select 
              id
            from 
              ineco_stock_report_problem 
        """
        cr.execute(sql)
        res = cr.fetchall()
        if not res:
            return [('id', '=', 0)]
        return [('id', 'in', [x[0] for x in res])]
        
    _name = 'ineco.stock.report'
    _description = 'Ineco Stock Reporting'
    _table = 'ineco_stock_report_master'
    #_auto = False
    _columns = {
        'location_dest_id': fields.many2one('stock.location','Location'),
        'lot_id': fields.many2one('stock.production.lot', 'Production Lot'),
        'expired': fields.date('Date Expired'),
        'tracking_id': fields.many2one('stock.tracking', 'Pack'),
        'product_id': fields.many2one('product.product', 'Product'),
        'uom_id': fields.many2one('product.uom', 'UOM'),
        #POP-028 
        'qty': fields.float('On Hand', digits_compute=dp.get_precision('Product UoM')),
        #POP-005
        'warehouse_uom': fields.many2one('product.uom', 'Warehouse UOM'),
        #POP-028 
        'warehouse_qty': fields.float('Warehouse Qty', digits_compute=dp.get_precision('Product UoM')),
        'date_input': fields.date('Lot Date'),
        #POP-028 
        'quantity': fields.float('Quantity', digits_compute=dp.get_precision('Product UoM')),
        'available': fields.function(_get_product_available,  string="Stock Move Quantity (Real Stock)", digits_compute=dp.get_precision('Product UoM'), type="float", method=True),
        'problemed': fields.function(_problemed, method=True, string='Problem', fnct_search=_problemed_search, type='boolean'),
        #POP-029
        'partial_uom': fields.many2one('product.uom', 'Partial UOM'),
        'partial_qty': fields.integer('Partial Qty'),
        'full_uom': fields.many2one('product.uom', 'Full UOM'),
        'full_qty': fields.integer('Full Qty'),        
    }
    
    _defaults = {
        'qty': 0,
        'quantity': 0,
    }

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
            
        for line in self.browse(cr, uid, ids):
            uom_obj = self.pool.get('product.uom')
            qty1 = uom_obj._compute_qty_obj(cr, uid, line.partial_uom, line.partial_qty, line.partial_uom, context=context ) or 0.0
            qty2 = uom_obj._compute_qty_obj(cr, uid, line.full_uom, line.full_qty, line.partial_uom, context=context ) or 0.0
            if line.available <> qty1 + qty2:
                full_qty = round(line.available // round(1/line.full_uom.factor)) or 0.0
                partial_qty = round(line.available - round( (full_qty / line.full_uom.factor), 10))
                vals['full_qty'] = full_qty
                vals['partial_qty'] = partial_qty 
                            
        return super(ineco_stock_report, self).write(cr, uid, ids, vals, context=context)

    def schedule_problem_sync(self, cr, uid, context=None):
        cr.execute("delete from ineco_stock_report_problem")
        cr.commit()
        sql = """
            insert into ineco_stock_report_problem
            select 
              id
            from ineco_stock_report_master 
            where
              qty <> 
              coalesce( (select sum(ineco_get_stock(stock_move.product_uom, stock_move.product_qty)) from stock_move 
               where 
                stock_move.location_id <> ineco_stock_report_master.location_dest_id
                  and stock_move.location_dest_id = ineco_stock_report_master.location_dest_id
                  and stock_move.product_id = ineco_stock_report_master.product_id
                  and stock_move.state = 'done'
                  and stock_move.prodlot_id = ineco_stock_report_master.lot_id
                  and coalesce(stock_move.tracking_id,'0') = coalesce(ineco_stock_report_master.tracking_id,'0')
               ),0) -
               coalesce((select sum(ineco_get_stock(stock_move.product_uom, stock_move.product_qty)) from stock_move 
               where 
                stock_move.location_id = ineco_stock_report_master.location_dest_id
                  and stock_move.location_dest_id <> ineco_stock_report_master.location_dest_id
                  and stock_move.product_id = ineco_stock_report_master.product_id
                  and stock_move.state = 'done'
                  and coalesce(stock_move.prodlot_id,'0') = coalesce(ineco_stock_report_master.lot_id,'0')
                  and coalesce(stock_move.tracking_id,'0') = coalesce(ineco_stock_report_master.tracking_id,'0')
               ),0)                 
        """
        cr.execute(sql)
        cr.commit()
        cr.execute("update ineco_stock_report_master set create_uid = 1, create_date = now()")
        cr.commit()
        
    #POP-031
    def schedule_correct_stock(self, cr, uid, context=None):
        stock_report_ids = self.pool.get('ineco.stock.report').search(cr, uid, [])
        for line in self.pool.get('ineco.stock.report').browse(cr, uid, stock_report_ids):
            uom_obj = self.pool.get('product.uom')
            if line.partial_uom and line.full_uom:
                qty1 = uom_obj._compute_qty_obj(cr, uid, line.partial_uom, line.partial_qty, line.partial_uom, context=context ) or 0.0
                qty2 = uom_obj._compute_qty_obj(cr, uid, line.full_uom, line.full_qty, line.partial_uom, context=context ) or 0.0
                if line.available <> qty1 + qty2:
                    full_qty = round(line.available // round(1/line.full_uom.factor)) or 0.0
                    partial_qty = round(line.available - round( (full_qty / line.full_uom.factor), 10))
                    line.write({'full_qty':full_qty,'partial_qty':partial_qty})

    
#    def schedule_sync(self, cr, uid, context=None):
    #   cr.execute("delete from ineco_stock_report")
    #   cr.commit()
    #   cr.execute("insert into ineco_stock_report select * from tmp_ineco_stock_report")
    #   cr.commit()
        
        

#        cr.execute("""
#            select * from ineco_stock_report
#        """)
#        cr.execute("""
#            create or replace view ineco_stock_report as (
#                select id, (a[id]).*
#                from (
#                    select a, generate_series(1, array_upper(a,1)) as id
#                        from (
#                            select array (
#                                select ineco_stock_report_template_c from ineco_stock_report_template_c
#
#                            ) as a
#                    ) b
#                ) c        
#            )
#        """)
ineco_stock_report()

#POP-011 -> Move omg.stock
#class ineco_query_stock_report(osv.osv):
#    _name = 'ineco.query.stock.report'
#    _description = 'Final Summary Stock Report'
#    _auto = False
    
#    def init(self,cr):
#        tools.drop_view_if_exists(cr, 'ineco_query_stock_report')
#        cr.execute("""
#            CREATE OR REPLACE VIEW ineco_query_stock_report AS 
#             SELECT pt.name_template AS customer_product_name, pp.name_template AS product_name, spl.name AS production_lot_id, spl.date_expired, st.name AS pack_id, sl.name AS location_id, sp.ineco_delivery_date::timestamp without time zone AS date_expected, pu.name AS uom_name, sm.product_qty, pu2.name AS warehouse_uom_name, ineco_convert_stock(pp.warehouse_uom, sm.product_qty::double precision) AS product_full_qty, sm.product_qty::double precision - ineco_get_stock(pp.warehouse_uom, ineco_convert_stock(pp.warehouse_uom, sm.product_qty::double precision)) AS product_split_qty, issc.name AS sticker_name, pp.warehouse_uom, sp.ineco_delivery_date
#               FROM stock_move sm
#               LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
#               LEFT JOIN product_product pp ON sm.product_id = pp.id
#               LEFT JOIN product_product pt ON sp.customer_product_id = pt.id
#               LEFT JOIN stock_production_lot spl ON sm.prodlot_id = spl.id
#               LEFT JOIN stock_tracking st ON sm.tracking_id = st.id
#               LEFT JOIN stock_location sl ON sm.location_id = sl.id
#               LEFT JOIN product_template ptt ON pp.id = ptt.id
#               LEFT JOIN product_uom pu ON ptt.uom_id = pu.id
#               LEFT JOIN product_uom pu2 ON pp.warehouse_uom = pu2.id
#               LEFT JOIN ineco_stock_sticker_category issc ON pp.sticker_category_id = issc.id
#              WHERE sp.type::text = 'out'::text AND sm.state::text <> 'cancel'::text
#              ORDER BY pp.sticker_category_id, sl.name, pt.name_template, spl.name DESC, st.name DESC, pp.name_template
#        """)
        
#ineco_query_stock_report()

#POP-009 move to product.py
#class ineco_stock_sticker(osv.osv):
#    _name = "ineco.stock.sticker.category"
#    _description = "Warehouse Delivery Sticker" 
#    _columns = {
#        'name': fields.char('Sticker Category', size=50, required=True),
#        'printable': fields.boolean('Printable'),
#        'active': fields.boolean('Active'),
#    }
#    _defaults = {
#        'printable': True,
#        'active': True,
#    }
#ineco_stock_sticker()

class stock_journal(osv.osv):
    _name = 'stock.journal'
    _description = 'Ineco Stock Journal'
    _inherit = 'stock.journal'
    
    _columns = {
        'sequence_id': fields.many2one('ir.sequence', 'Sequence', required=True),
        'location_available': fields.boolean('Location Available')
    }
    _default = {
        'location_available': False
    }
    
stock_journal()

#POP-012
class ineco_stock_barcode_delivery(osv.osv):
    
    _name = 'ineco.stock.barcode.delivery'
    _description = 'Barcode Delivery'
    _columns = {
        'name': fields.char('Description', size=128),
        'tracking_id': fields.many2one('stock.tracking','Pack', required=True),
        'product_id': fields.many2one('product.product', 'Product'),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure'),
        'quantity': fields.float('Quantity',required=True, digits=(12, 2)),
        'date_barcode': fields.datetime('Date', required=True),
        'location_id': fields.many2one('stock.location','Location', required=True),
        'user_id': fields.many2one('res.users', 'User', required=True),
        'move_id': fields.many2one('stock.move', 'Move'),
        'lot_id': fields.many2one('stock.production.lot','Lot',required=True),
    }
    
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        "date_barcode": time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    _order = "date_barcode desc"

    def create(self, cr, uid, vals, context=None):
        vals.update({'date_barcode': time.strftime('%Y-%m-%d %H:%M:%S')})
        tracking_id = vals['tracking_id']
        track = self.pool.get('stock.tracking').browse(cr, uid, [tracking_id])
        if track:
            inventory_ids = self.pool.get('ineco.stock.report').search(cr, uid, [('location_dest_id','=',vals['location_id']),('tracking_id','=',tracking_id),('product_id','=',vals['product_id']),('qty','>',0)])
            stock = self.pool.get('ineco.stock.report').browse(cr, uid, inventory_ids)[0]
            if stock:
                if stock.qty < vals['quantity']:
                    raise osv.except_osv(_('Error !'), _('Stock Unavailable.'))
            location_ids = self.pool.get('stock.location').search(cr, uid, [('name','=','Output')])
            if location_ids:
                location_out = self.pool.get('stock.location').browse(cr, uid, location_ids)[0]
#                cr.execute("""
#                    select ir.product_id, ir.tracking_id, ir.uom_id, pt.name, ir.qty, ir.location_dest_id from tmp_ineco_stock_report ir
#                      left join stock_tracking st on ir.tracking_id = st.id
#                      left join product_template pt on ir.product_id = pt.id
#                    where ir.tracking_id = %s
#                """ % (track[0].id) )
                move_id = self.pool.get('stock.move').create(cr, uid, {
                    'name': 'barcode',
                    'picking_id': False,
                    'product_id': vals['product_id'],
                    #POP-018
                    'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'date_expected': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'product_qty': vals['quantity'] or 0.0,
                    'product_uom': vals['uom_id'],
                    'location_id': vals['location_id'],
                    'location_dest_id': location_out.id,
                    'tracking_id': vals['tracking_id'],
                    'prodlot_id': vals['lot_id'],
                    'state': 'draft',
                    'note': False,
                })
                vals.update({'move_id': move_id})
            else:
                raise osv.except_osv(_('Error !'), _('Output Location cannot set.'))
            self.pool.get('stock.move').browse(cr, uid, move_id).write({'state':'done'})
        return super(ineco_stock_barcode_delivery, self).create(cr, uid, vals, context=context) 

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        barcode = self.pool.get('ineco.stock.barcode.delivery').browse(cr, uid, ids)[0]
        if barcode and barcode.move_id:
            stock_move = self.pool.get('stock.move').browse(cr, uid, [barcode.move_id.id])[0]
            if stock_move:
                stock_move.write({'product_qty': vals['quantity'],'state':'done'})
        return super(ineco_stock_barcode_delivery, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        barcode = self.pool.get('ineco.stock.barcode.delivery').browse(cr, uid, ids)[0]
        if barcode and barcode.move_id:
            stock_move = self.pool.get('stock.move').browse(cr, uid, [barcode.move_id.id])[0]
            if stock_move:
                stock_move.write({'state': 'cancel'})        
        return super(ineco_stock_barcode_delivery, self).unlink(cr, uid, ids, context=context)
    
    def onchange_tracking_id(self, cr, uid, ids, tracking_id=False, context=None):
        if not context:
            context = {}
        if not tracking_id:
            return {}
        result = {}
        track_obj = self.pool.get('stock.tracking')
        track = track_obj.browse(cr, uid, [tracking_id], context=context)[0]
        stock = False
        if track:
            stock_ids = self.pool.get('stock.location').search(cr, uid, [('name','=','Stock'),('company_id','=',False)])
            if stock_ids:
                inventory_ids = self.pool.get('ineco.stock.report').search(cr, uid, [('location_dest_id','child_of',stock_ids[0]),('tracking_id','=',track.id),('qty','>',0)])
                stock = self.pool.get('ineco.stock.report').browse(cr, uid, inventory_ids)
#                select ir.product_id, ir.tracking_id, ir.uom_id, pt.name, ir.qty, ir.location_dest_id, ir.lot_id from tmp_ineco_stock_report ir
#            cr.execute("""
#                select ir.product_id, ir.tracking_id, ir.uom_id, pt.name, ir.qty, ir.location_dest_id, ir.lot_id from ineco_stock_report_master ir
#                  left join stock_tracking st on ir.tracking_id = st.id
#                  left join product_template pt on ir.product_id = pt.id
#                where ir.tracking_id = %s and ir.qty > 0
#                """ % (track.id) )
#            stock = cr.dictfetchall()
            if stock:
                data = stock[0]
                if data['qty'] and data['qty'] > 0 :
                    result = {
                        'name': data.product_id.name,
                        'product_id': data.product_id.id,
                        'quantity': data.qty,
                        'uom_id': data.uom_id.id,
                        'location_id': data.location_dest_id.id,
                        'lot_id': data.lot_id.id,
                    }
#                    result = {
#                        'name': data['name'] ,
#                        'product_id':  data['product_id'],
#                        'quantity': data['qty'],
#                        'uom_id': data['uom_id'],
#                        'location_id': data['location_dest_id'],
#                        'lot_id': data['lot_id']}
                else:
                    raise osv.except_osv(_('Error !'), _('Not have stock!'))
        else:
            raise osv.except_osv(_('Error !'), _('Pack Not Found!'))
        
        return {'value': result}
    
ineco_stock_barcode_delivery()

#POP-016
class ineco_stock_barcode_move(osv.osv):
    
    _name = 'ineco.stock.barcode.move'
    _description = 'Barcode Move'
    _columns = {
        'name': fields.char('Description', size=128),
        'tracking_id': fields.many2one('stock.tracking','Pack', required=True),
        'product_id': fields.many2one('product.product', 'Product'),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure'),
        'quantity': fields.float('Quantity',required=True, digits=(12, 2)),
        'date_barcode': fields.datetime('Date', required=True),
        'location_id': fields.many2one('stock.location','Location', required=True),
        'user_id': fields.many2one('res.users', 'User', required=True),
        'move_id': fields.many2one('stock.move', 'Move'),
        'lot_id': fields.many2one('stock.production.lot','Lot',required=True),
    }
    
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        "date_barcode": time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    _order = "date_barcode desc"

    def create(self, cr, uid, vals, context=None):
        vals.update({'date_barcode': time.strftime('%Y-%m-%d %H:%M:%S')})
        tracking_id = vals['tracking_id']
        track = self.pool.get('stock.tracking').browse(cr, uid, [tracking_id])
        if track:
            location_ids = self.pool.get('stock.location').search(cr, uid, [('name','=','Output')])
            if location_ids:
                location_out = self.pool.get('stock.location').browse(cr, uid, location_ids)[0]
#                cr.execute("""
#                    select ir.product_id, ir.tracking_id, ir.uom_id, pt.name, ir.qty, ir.location_dest_id from tmp_ineco_stock_report ir
#                      left join stock_tracking st on ir.tracking_id = st.id
#                      left join product_template pt on ir.product_id = pt.id
#                    where ir.tracking_id = %s
#                """ % (track[0].id) )
                move_id = self.pool.get('stock.move').create(cr, uid, {
                    'name': 'barcode moving',
                    'picking_id': False,
                    'product_id': vals['product_id'],
                    'date': time.strftime('%Y-%m-%d'),
                    'date_expected': time.strftime('%Y-%m-%d'),
                    'product_qty': vals['quantity'] or 0.0,
                    'product_uom': vals['uom_id'],
                    'location_id': location_out.id,
                    'location_dest_id': vals['location_id'] ,
                    'tracking_id': vals['tracking_id'],
                    'prodlot_id': vals['lot_id'],
                    'state': 'done',
                    'note': False,
                })
                vals.update({'move_id': move_id})
            else:
                raise osv.except_osv(_('Error !'), _('Output Location cannot set.'))

        return super(ineco_stock_barcode_move, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        barcode = self.pool.get('ineco.stock.barcode.move').browse(cr, uid, ids)[0]
        if barcode and barcode.move_id:
            stock_move = self.pool.get('stock.move').browse(cr, uid, [barcode.move_id.id])[0]
            if stock_move:
                stock_move.write({'product_qty': vals['quantity']})
        return super(ineco_stock_barcode_move, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        barcode = self.pool.get('ineco.stock.barcode.move').browse(cr, uid, ids)[0]
        if barcode and barcode.move_id:
            stock_move = self.pool.get('stock.move').browse(cr, uid, [barcode.move_id.id])[0]
            if stock_move:
                stock_move.write({'state': 'cancel'})        
        return super(ineco_stock_barcode_move, self).unlink(cr, uid, ids, context=context)
    
    def onchange_tracking_id(self, cr, uid, ids, tracking_id=False, context=None):
        if not context:
            context = {}
        if not tracking_id:
            return {}
        result = {}
        track_obj = self.pool.get('stock.tracking')
        track = track_obj.browse(cr, uid, [tracking_id], context=context)[0]
        if track:
            cr.execute("""
                select 
                  sm.product_id,
                  sm.product_uom,
                  sm.prodlot_id,
                  sm.location_id,
                  sm.name
                from stock_tracking st
                join stock_move sm on st.id = sm.tracking_id
                where st.id = %s 
                order by sm.create_date desc
                limit 1            
            """ % (track.id) )
            #cr.execute("""
            #    select ir.product_id, ir.tracking_id, ir.uom_id, pt.name, ir.qty, ir.location_dest_id, ir.lot_id from tmp_ineco_stock_report ir
            #      left join stock_tracking st on ir.tracking_id = st.id
            #      left join product_template pt on ir.product_id = pt.id
            #    where ir.tracking_id = %s
            #    """ % (track.id) )
            stock = cr.dictfetchall()
            if stock:
                data = stock[0]
                result = {
                    'name': data['name'] ,
                    'product_id':  data['product_id'],
                    'quantity': 0,
                    'uom_id': data['product_uom'],
                    'location_id': False,
                    'lot_id': data['prodlot_id']}
        else:
            raise osv.except_osv(_('Error !'), _('Pack Not Found!'))
        
        return {'value': result}
    
ineco_stock_barcode_move()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

