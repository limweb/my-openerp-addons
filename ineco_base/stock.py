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
# 08-03-2012       POP-013    Make performace auto picking
# 10-03-2012       POP-014    Change Split in Auto Picking -> Valid by Do it Again
# 14-03-2012       POP-015    Change way to force compute with delivery
# 16-03-2012       POP-015    Change Set to Confirm -> Set To Draft
# 30-03-2012       POP-016    Create ienco.stock.barcode.move
# 05-04-2012       POP-017    Add Return Columns in Stock Picking

import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp
import netsvc

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from operator import itemgetter
from itertools import groupby

class stock_inventory(osv.osv):
    
    _name = "stock.inventory"
    _inherit = "stock.inventory"
    _description = "Stock Inventory"    

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
                stock_report_ids = self.pool.get('ineco.stock.report').search(cr, uid, 
                    [('location_dest_id','=',line.location_id.id),('product_id','=',line.product_id.id)])
                amount = 0
                if stock_report_ids:
                    stock_report = self.pool.get('ineco.stock.report').browse(cr, uid, stock_report_ids)[0]
                    amount = stock_report.qty                    
                    #amount = location_obj._product_get(cr, uid, line.location_id.id, [pid], product_context)[pid]

                change = line.product_qty - amount
                lot_id = line.prod_lot_id.id
                if change:
                    location_id = line.product_id.product_tmpl_id.property_stock_inventory.id
                    value = {
                        'name': 'INV:' + str(line.inventory_id.id) + ':' + line.inventory_id.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'prodlot_id': lot_id,
                        'tracking_id': line.tracking_id.id,
                        'date': inv.date,
                    }
                    if change > 0:
                        value.update( {
                            'product_qty': change,
                            'location_id': location_id,
                            'location_dest_id': line.location_id.id,
                        })
                    else:
                        value.update( {
                            'product_qty': -change,
                            'location_id': line.location_id.id,
                            'location_dest_id': location_id,
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
        'tracking_id': fields.many2one('stock.tracking', 'Pack')
    }

    def on_change_product_id(self, cr, uid, ids, location_id, product, uom=False, to_date=False):
        if not product:
            return {}
        uom_categ_id = None
        if not uom:
            prod = self.pool.get('product.product').browse(cr, uid, [product], {'uom': uom})[0]
            uom = prod.uom_id.id
            uom_categ_id = prod.uom_id.category_id.id
        stock_report_ids = self.pool.get('ineco.stock.report').search(cr, uid, [('location_dest_id','=',location_id),('product_id','=',product)])
        lot_id = False
        tracking_id = False
        amount = 0
        if stock_report_ids:
            stock_report = self.pool.get('ineco.stock.report').browse(cr, uid, stock_report_ids)[0]
            amount = stock_report.qty
            lot_id = stock_report.lot_id.id
            tracking_id = stock_report.tracking_id.id
        #amount = self.pool.get('stock.location')._product_get(cr, uid, location_id, [product], {'uom': uom, 'to_date': to_date})[product]
        result = {'product_qty': amount, 'product_uom': uom,'uom_category_id': uom_categ_id,'tracking_id':tracking_id,'prod_lot_id':lot_id}
        return {'value': result}

stock_inventory_line()

class stock_move(osv.osv):

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
    }

    _defaults = {
        'location_dest_id': _ineco_default_location_destination,
    }

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if 'product_id' in vals and 'product_qty' in vals:
            product_obj = self.pool.get('product.product').browse(cr, uid, vals['product_id'])
            warehouse_uom_id = product_obj.warehouse_uom.id
            product_qty = vals['product_qty']
            warehouse_qty = product_qty
            diff = 0
            if warehouse_uom_id:
                cr.execute("select ineco_convert_stock(%s, %s)" % (warehouse_uom_id, product_qty)) 
                warehouse_res = cr.fetchone()
                if warehouse_res:
                    warehouse_qty = warehouse_res[0]
                    cr.execute("select ineco_get_stock(%s, %s)" % (warehouse_uom_id, warehouse_qty))
                    stock_res = cr.fetchone()
                    if stock_res:
                        full_qty = stock_res[0]
                        if full_qty > product_qty:
                            warehouse_qty = warehouse_qty - 1
                cr.execute("select ineco_get_stock(%s, %s)" % (warehouse_uom_id, warehouse_qty))
                diff_res = cr.fetchone()
                #diff = 0
                if diff_res:
                    diff = product_qty - diff_res[0] 
            vals.update({'warehouse_uom': warehouse_uom_id,'warehouse_qty': warehouse_qty,'warehouse_diff': diff})
        return super(stock_move, self).write(cr, uid, ids, vals, context=context)
    
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
        if not ids:
            result['name'] = product.partner_ref
        if loc_id:
            result['location_id'] = loc_id
        if loc_dest_id:
            result['location_dest_id'] = loc_dest_id
        return {'value': result}

    def check_assign(self, cr, uid, ids, context=None):
        """ Checks the product type and accordingly writes the state.
        @return: No. of moves done
        """
        done = []
        count = 0
        pickings = {}
        if context is None:
            context = {}
        for move in self.browse(cr, uid, ids, context=context):
            if not ((move.prodlot_id and move.tracking_id) or move.picking_id.ineco_return) :
                if move.product_id.type == 'service' or move.location_id.usage == 'supplier':
                    if move.state in ('confirmed', 'waiting'):
                        done.append(move.id)
                    pickings[move.picking_id.id] = 1
                    continue
                if move.state in ('confirmed', 'waiting'):
                    #POP-013
                    delete_sql = """
                        delete from ineco_stock_tracking_line
                        where id not in (
                            select a.id from ineco_stock_tracking_line a
                            join stock_move b on a.move_id = b.id and a.tracking_id = b.tracking_id and b.state <> 'cancel')
                    """
                    cr.execute(delete_sql)
                    cr.commit()
                    #POP-003 
                    search_sql = """
                        select 
                          ineco_stock_report.id,
                          ineco_stock_report.location_dest_id,
                          ineco_stock_report.lot_id,
                          ineco_stock_report.expired,
                          ineco_stock_report.tracking_id,
                          ineco_stock_report.product_id,
                          ineco_stock_report.uom_id,
                          ineco_stock_report.qty, 
                          ineco_get_stock(uom_id, qty) as total,
                          coalesce((select sum(product_qty) as total from ineco_stock_tracking_line
                            join stock_move on ineco_stock_tracking_line.move_id = stock_move.id
                            where ineco_stock_tracking_line.tracking_id = ineco_stock_report.tracking_id),0) as usage,
                          ineco_get_stock(uom_id, qty) -
                          coalesce((select sum(product_qty) as total from ineco_stock_tracking_line
                            join stock_move on ineco_stock_tracking_line.move_id = stock_move.id
                            where ineco_stock_tracking_line.tracking_id = ineco_stock_report.tracking_id),0) as available
                        from ineco_stock_report
                        join stock_production_lot on ineco_stock_report.lot_id = stock_production_lot.id
                        join stock_tracking on ineco_stock_report.tracking_id = stock_tracking.id
                        where ineco_stock_report.product_id = %s and
                          ineco_get_stock(uom_id, qty) -
                          coalesce((select sum(product_qty) as total from ineco_stock_tracking_line
                           join stock_move on ineco_stock_tracking_line.move_id = stock_move.id
                           where ineco_stock_tracking_line.tracking_id = ineco_stock_report.tracking_id),0) > 0
                        order by ineco_stock_report.expired, stock_production_lot.date, stock_tracking.name                                 
                    """
                    cr.execute(search_sql % move.product_id.id)
                    stock_list = cr.dictfetchall()
                    balance_qty = move.product_qty
                    last_move_id = move.id
                    for list in stock_list:
                        if balance_qty > 0:
                            balance_qty = balance_qty - list['available']
                            if balance_qty > 0:
                                tracking_line_qty = list['available']
                                self.write(cr, uid, [last_move_id], {
                                    'product_qty':tracking_line_qty,
                                    'prodlot_id': list['lot_id'],
                                    'state':'assigned',
                                    'tracking_id': list['tracking_id'],
                                    'location_id':list['location_dest_id']})
                                tracking_line = self.pool.get('ineco.stock.tracking.line')
                                tracking_line.create(cr, uid, {
                                    'name': move.product_id.name,
                                    'move_id': last_move_id,
                                    'tracking_id': list['tracking_id']
                                })
                                #last_move_id = self.copy(cr, uid, last_move_id, {'product_qty': balance_qty,'state':'assigned','location_id':list['location_dest_id']})
                                #POP-014
                                last_move_id = self.copy(cr, uid, last_move_id, {'product_qty': balance_qty})
                            else:
                                self.write(cr, uid, [last_move_id], {
                                    'state':'assigned',
                                    'prodlot_id': list['lot_id'],
                                    'tracking_id': list['tracking_id'],
                                    'location_id': list['location_dest_id']})
    
                                tracking_line = self.pool.get('ineco.stock.tracking.line')
                                tracking_line.create(cr, uid, {
                                    'name': move.product_id.name,
                                    'move_id': last_move_id,
                                    'tracking_id': list['tracking_id']
                                })
                    pickings[move.picking_id.id] = 1
            else:
                done.append(move.id)
                pickings[move.picking_id.id] = 1
        if done:
            self.write(cr, uid, done, {'state':'assigned'})
                    
                # Important: we must pass lock=True to _product_reserve() to avoid race conditions and double reservations
                #res = self.pool.get('stock.location')._product_reserve(cr, uid, [move.location_id.id], move.product_id.id, move.product_qty, {'uom': move.product_uom.id}, lock=True)
                #if res:
                    #_product_available_test depends on the next status for correct functioning
                    #the test does not work correctly if the same product occurs multiple times
                    #in the same order. This is e.g. the case when using the button 'split in two' of
                    #the stock outgoing form
                #    self.write(cr, uid, [move.id], {'state':'assigned'})
                #    done.append(move.id)
                #    pickings[move.picking_id.id] = 1
                #    r = res.pop(0)
                #    cr.execute('update stock_move set location_id=%s, product_qty=%s where id=%s', (r[1], r[0], move.id))

                #    while res:
                #        r = res.pop(0)
                #        move_id = self.copy(cr, uid, move.id, {'product_qty': r[0], 'location_id': r[1]})
                #        done.append(move_id)
                #Important - End
    
        cando = True
        for move in self.browse(cr, uid, ids, context=context):
            if cando:
                if move.state in ('confirmed', 'waiting'):
                    cando = False
        #new by pop
        if cando:
            for pick_id in pickings:
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_write(uid, 'stock.picking', pick_id, cr)
                
        #if count:
        #    for pick_id in pickings:
        #        wf_service = netsvc.LocalService("workflow")
                #mark by pop
                #wf_service.trg_write(uid, 'stock.picking', pick_id, cr)
        return count

           
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

    #POP-008 Add new sequence by stock journal 
    def create(self, cr, user, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            if ('stock_journal_id' in vals) and (vals.get('stock_journal_id')):
                stock_journal = self.pool.get('stock.journal').browse(cr, user, [vals.get('stock_journal_id')])[0]
                if stock_journal:
                    seq_obj_name = stock_journal.sequence_id.code
                else:
                    seq_obj_name =  'stock.picking.' + vals['type']
            elif ('stock_journal_id' in context):
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
        user = self.pool.get('res.users').browse(cr, uid, uid)
        for pick in self.browse(cr, uid, ids, context=context):
            todo = []
            for move in pick.move_lines:
                if user.company_id.skip_stock_report or pick.ineco_return:
                    if move.state == 'assigned':
                        todo.append(move.id)
                else:
                    #POP-014
                    #if pick.type in ['out','internal']:
                    if pick.type in ['internal']:
                        check_ids = self.pool.get('ineco.stock.report').search(cr, uid, [('product_id','=',move.product_id.id),('location_dest_id','=',move.location_id.id)])
                        if check_ids:
                            stock_qty = 0
                            for stock in self.pool.get('ineco.stock.report').browse(cr, uid, check_ids): 
                                stock_qty = stock_qty + stock.qty
                            sql = """
                            select ineco_get_stock(%s, %s) as total
                            """
                            cr.execute(sql % (move.product_uom.id, str(int(move.product_qty))))
                            total = cr.dictfetchall()
                            product_qty = 0
                            if total:
                                product_qty = total[0]['total']
                                if stock_qty >= product_qty: #change in default_uom qty 
                                    if move.state == 'assigned':
                                        todo.append(move.id)
    #                            else:
    #                                raise osv.except_osv(_('Error !'), _('Stock insufficient in source location. [' + move.product_id.name + '->'+move.location_id.name+']'))
    #                    else:
    #                        raise osv.except_osv(_('Error !'), _('Can not found stock in source location.'))
                    else:
                        if move.state == 'assigned':
                            todo.append(move.id)
            if len(todo):
                self.pool.get('stock.move').action_done(cr, uid, todo,
                        context=context)
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

    def _get_stock(self, cr, uid, ids, field_name, arg, context=None):
        """ Gets stock of products for locations
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        if 'location_id' not in context:
            locations = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')], context=context)
        else:
            locations = context['location_id'] and [context['location_id']] or []

        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}.fromkeys(ids, 0.0)
        if locations:
            cr.execute('''select
                    lot_id,
                    sum(ineco_get_stock(uom_id,qty))
                from
                    ineco_stock_report
                where
                    location_dest_id IN %s and lot_id IN %s group by lot_id''',(tuple(locations),tuple(ids),))
            res.update(dict(cr.fetchall()))

        return res

    def _stock_search(self, cr, uid, obj, name, args, context=None):
        """ Searches Ids of products
        @return: Ids of locations
        """
        locations = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')])
        cr.execute('''select
                lot_id,
                sum(ineco_get_stock(uom_id,qty))
            from
                ineco_stock_report
            where
                location_dest_id IN %s group by lot_id
            having  sum(ineco_get_stock(uom_id,qty)) '''+ str(args[0][1]) + str(args[0][2]),(tuple(locations),))
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
    }
    
    _defaults = {
        "date_expired": time.strftime('%Y-%m-%d')
    }
    
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
#        'ineco_stock_real': fields.function(_product_value, store=True, method=True, type='float', string='Real Stock', multi="stock"),
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
                    ineco_stock_report
                where
                    tracking_id IN %s group by tracking_id''',(tuple(tracking),))
            res.update(dict(cr.fetchall()))

        return res

    _columns = {
        'stock_available': fields.function(_get_stock, method=True, type="float", string="Available",
            help="Current quantity of products with this Pack No available in company warehouses",
            digits_compute=dp.get_precision('Product UoM')),
##        'track_line_ids': fields.one2many('ineco.stock.tracking.line','tracking_id','History'),
    }
    
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
        cr.execute("select count(1) from pg_class where relkind=%s and relname=%s", ('r', 'ineco_stock_report'))
        if cr.fetchone()[0]:
            cr.execute("DROP table %s" % ('ineco_stock_report'))
            cr.commit()

        cr.execute("select * into ineco_stock_report from tmp_ineco_stock_report")

ineco_stock_report_template_d()

class ineco_stock_report(osv.osv):
        
    _name = 'ineco.stock.report'
    _description = 'Stock Reporting'
    _auto = False
    _columns = {
        'location_dest_id': fields.many2one('stock.location','Location'),
        'lot_id': fields.many2one('stock.production.lot', 'Production Lot'),
        'expired': fields.date('Date Expired'),
        'tracking_id': fields.many2one('stock.tracking', 'Pack'),
        'product_id': fields.many2one('product.product', 'Product'),
        'uom_id': fields.many2one('product.uom', 'UOM'),
        'qty': fields.float('Quantity'),
        #POP-005
        'warehouse_uom': fields.many2one('product.uom', 'Warehouse UOM'),
        'warehouse_qty': fields.float('Warehouse Qty'),
        'date_input': fields.date('Lot Date'),
    }
    
    def schedule_sync(self, cr, uid, context=None):
        cr.execute("delete from ineco_stock_report")
        cr.commit()
        cr.execute("insert into ineco_stock_report select * from tmp_ineco_stock_report")
        cr.commit()

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
        'sequence_id': fields.many2one('ir.sequence', 'Sequence', required=True)
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
                    'date': time.strftime('%Y-%m-%d'),
                    'date_expected': time.strftime('%Y-%m-%d'),
                    'product_qty': vals['quantity'] or 0.0,
                    'product_uom': vals['uom_id'],
                    'location_id': vals['location_id'],
                    'location_dest_id': location_out.id,
                    'tracking_id': vals['tracking_id'],
                    'prodlot_id': vals['lot_id'],
                    'state': 'done',
                    'note': False,
                })
                vals.update({'move_id': move_id})
            else:
                raise osv.except_osv(_('Error !'), _('Output Location cannot set.'))

        return super(ineco_stock_barcode_delivery, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        barcode = self.pool.get('ineco.stock.barcode.delivery').browse(cr, uid, ids)[0]
        if barcode and barcode.move_id:
            stock_move = self.pool.get('stock.move').browse(cr, uid, [barcode.move_id.id])[0]
            if stock_move:
                stock_move.write({'product_qty': vals['quantity']})
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
        if track:
            cr.execute("""
                select ir.product_id, ir.tracking_id, ir.uom_id, pt.name, ir.qty, ir.location_dest_id, ir.lot_id from tmp_ineco_stock_report ir
                  left join stock_tracking st on ir.tracking_id = st.id
                  left join product_template pt on ir.product_id = pt.id
                where ir.tracking_id = %s
                """ % (track.id) )
            stock = cr.dictfetchall()
            if stock:
                data = stock[0]
                if data['qty'] and data['qty'] > 0 :
                    result = {
                        'name': data['name'] ,
                        'product_id':  data['product_id'],
                        'quantity': data['qty'],
                        'uom_id': data['uom_id'],
                        'location_id': data['location_dest_id'],
                        'lot_id': data['lot_id']}
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

