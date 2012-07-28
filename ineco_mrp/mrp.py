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

# 19-06-2012     POP-001    Initialization
# 10-07-2012     POP-002    Add Planned Date
# 14-07-2012     POP-003    Change SM State Default, Add Category ID
# 20-07-2012     POP-004    Add Default Lot ID
# 21-07-2012     POP-005    Change Transfer Journal
# 24-07-2012     POP-006    Add Expired Date Lot By WIP
# 25-07-2012     POP-007    Add Lot Name By WIP
# 28-07-2012     POP-008    Default Category UOM

from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import osv, fields
from tools.translate import _
import netsvc
import time
import tools

def rounding(f, r):
    if not r:
        return f
    return round(f / r) * r

class mrp_bom(osv.osv):
    
    _name = 'mrp.bom'
    _inherit = 'mrp.bom'
    _description = 'Override method for extract bom master'
    _columns = {}
    
    def _bom_explode(self, cr, uid, bom, factor, properties=[], addthis=False, level=0):
        """ Finds Products and Work Centers for related BoM for manufacturing order.
        @param bom: BoM of particular product.
        @param factor: Factor of product UoM.
        @param properties: A List of properties Ids.
        @param addthis: If BoM found then True else False.
        @param level: Depth level to find BoM lines starts from 10.
        @return: result: List of dictionaries containing product details.
                 result2: List of dictionaries containing Work Center details.
        """
        factor = factor / (bom.product_efficiency or 1.0)
        factor = rounding(factor, bom.product_rounding)
        if factor < bom.product_rounding:
            factor = bom.product_rounding
        result = []
        result2 = []
        result3 = {}
        phantom = False
        if bom.type == 'phantom' and not bom.bom_lines:
            newbom = self._bom_find(cr, uid, bom.product_id.id, bom.product_uom.id, properties)
            if newbom:
                res = self._bom_explode(cr, uid, self.browse(cr, uid, [newbom])[0], factor*bom.product_qty, properties, addthis=True, level=level+10)
                result = result + res[0]
                result2 = result2 + res[1]
                result3 = result3 + res[2]
                phantom = True
            else:
                phantom = False
        if not phantom:
            if addthis and not bom.bom_lines:
                result.append(
                {
                    'name': bom.product_id.name,
                    'product_id': bom.product_id.id,
                    'product_qty': bom.product_qty * factor,
                    'product_uom': bom.product_uom.id,
                    'product_uos_qty': bom.product_uos and bom.product_uos_qty * factor or False,
                    'product_uos': bom.product_uos and bom.product_uos.id or False,
                })
                #POP-005
                if bom.bom_id:
                    if bom.product_id.ineco_stock_journal_id:
                        result3[bom.product_id.ineco_stock_journal_id.id] = []
                        data = {
                            'product_id': bom.product_id.id,
                            'product_qty': bom.product_qty * factor,
                            'product_uom': bom.product_uom.id,
                        }
                        result3[bom.product_id.ineco_stock_journal_id.id] = [data]
                else:
                    if bom.product_id.ineco_stock_journal_id:
                        result3[bom.product_id.ineco_stock_transfer_journal_id.id] = []
                        data = {
                            'product_id': bom.product_id.id,
                            'product_qty': bom.product_qty * factor,
                            'product_uom': bom.product_uom.id,
                        }
                        result3[bom.product_id.ineco_stock_transfer_journal_id.id] = [data]
            if bom.routing_id:
                for wc_use in bom.routing_id.workcenter_lines:
                    wc = wc_use.workcenter_id
                    d, m = divmod(factor, wc_use.workcenter_id.capacity_per_cycle)
                    mult = (d + (m and 1.0 or 0.0))
                    cycle = mult * wc_use.cycle_nbr
                    result2.append({
                        'name': tools.ustr(wc_use.name) + ' - '  + tools.ustr(bom.product_id.name),
                        'workcenter_id': wc.id,
                        'sequence': level+(wc_use.sequence or 0),
                        'cycle': cycle,
                        'hour': float(wc_use.hour_nbr*mult + ((wc.time_start or 0.0)+(wc.time_stop or 0.0)+cycle*(wc.time_cycle or 0.0)) * (wc.time_efficiency or 1.0)),
                    })
            for bom2 in bom.bom_lines:
                res = self._bom_explode(cr, uid, bom2, factor, properties, addthis=True, level=level+10)
                result = result + res[0]
                result2 = result2 + res[1]
                if res[2]:
                    for key, value in res[2].iteritems():
                        result3[key] = result3.get(key, [])
                        result3[key] += value
        return result, result2, result3    
    
mrp_bom()


class mrp_production(osv.osv):

    _name = 'mrp.production'
    _inherit = 'mrp.production'
    _description = 'Manufacturing Order'
    _columns = {
        'ineco_stock_picking_ids': fields.one2many('stock.picking','production_id','Stock Picking'),
        'category_id': fields.many2one('product.uom.categ', 'UOM Category', ondelete="restrict"),
    }

    #POP-008
    def product_id_change(self, cr, uid, ids, product_id, context=None):
        """ Finds UoM of changed product.
        @param product_id: Id of changed product.
        @return: Dictionary of values.
        """
        if not product_id:
            return {'value': {
                'product_uom': False,
                'bom_id': False,
                'routing_id': False
            }}
        bom_obj = self.pool.get('mrp.bom')
        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        bom_id = bom_obj._bom_find(cr, uid, product.id, product.uom_id and product.uom_id.id, [])
        routing_id = False
        if bom_id:
            bom_point = bom_obj.browse(cr, uid, bom_id, context=context)
            routing_id = bom_point.routing_id.id or False
        result = {
            'product_uom': product.uom_id and product.uom_id.id or False,
            'category_id': product.uom_id and product.uom_id.category_id and product.uom_id.category_id.id or False,
            'bom_id': bom_id,
            'routing_id': routing_id
        }

        return {'value': result}

    def action_produce(self, cr, uid, production_id, production_qty, production_mode, context=None):
        production = self.browse(cr, uid, production_id, context=context)
        product = production.product_id
        #POP-006,007
        wip_expired_date = False
        lot_name = False
        for pick in production.ineco_stock_picking_ids:
            if pick.stock_journal_id.ineco_stock_type == 'wip' and pick.stock_journal_id.name == 'WIP'and not wip_expired_date:
                for move in pick.move_lines:
                    if not wip_expired_date:
                        wip_expired_date = move.prodlot_id.date_expired
                        lot_name = move.prodlot_id.name 
                        
        uom = production.product_uom
        stock_move_obj = self.pool.get('stock.move')
        stock_move_ids = self.pool.get('stock.move').search(cr, uid, 
            [('product_id','=',product.id),('production_id','=',production.id),('state','in',['waiting'])])
        if stock_move_ids:
            balance_qty = production_qty
            for sm in self.pool.get('stock.move').browse(cr, uid, stock_move_ids):
                #POP-004
                if wip_expired_date and sm.picking_id.stock_journal_id.ineco_use_expire:
                    context['wip_expired_date'] = wip_expired_date
                    context['lot_name'] = lot_name 
                product_val = {
                    'product_id': sm.product_id.id,
                }
                prolot_id = self.pool.get('stock.production.lot').create(cr, uid, product_val, context=context)
                if balance_qty >= sm.product_qty:
                    sm.write({'product_qty':balance_qty,'state':'assigned','prodlot_id':prolot_id})
                else:
                    default_val = {
                       'product_qty': balance_qty,
                       'state': 'assigned',
                       'prodlot_id':prolot_id,
                    }
                    balance_qty = sm.product_qty - balance_qty 
                    if balance_qty > 0:
                        new_sm_id = stock_move_obj.copy(cr, uid, sm.id, default_val)
                        sm.write({'product_qty':balance_qty})
        stock_move_all_ids = self.pool.get('stock.move').search(cr, uid, 
                        [('product_id','=',product.id),('production_id','=',production.id)])
        result = True
        for sm in self.pool.get('stock.move').browse(cr, uid, stock_move_all_ids):
            if sm.state in ['draft','waiting','assigned']:
                result = False
        if result:
            production.write({'state': 'done', 'date_finish': time.strftime('%Y-%m-%d %H:%M:%S')})        
            
        return True 
    
    def action_compute(self, cr, uid, ids, properties=[]):
        """ Computes bills of material of a product.
        @param properties: List containing dictionaries of properties.
        @return: No. of products.
        """
        results = []
        bom_obj = self.pool.get('mrp.bom')
        uom_obj = self.pool.get('product.uom')
        prod_line_obj = self.pool.get('mrp.production.product.line')
        workcenter_line_obj = self.pool.get('mrp.production.workcenter.line')
        stock_picking_obj = self.pool.get("stock.picking")
        stock_move_obj = self.pool.get('stock.move')
        for production in self.browse(cr, uid, ids):
            cr.execute('delete from mrp_production_product_line where production_id=%s', (production.id,))
            cr.execute('delete from mrp_production_workcenter_line where production_id=%s', (production.id,))
            cr.execute('delete from stock_picking where production_id=%s', (production.id,))
            bom_point = production.bom_id
            bom_id = production.bom_id.id
            if not bom_point:
                bom_id = bom_obj._bom_find(cr, uid, production.product_id.id, production.product_uom.id, properties)
                if bom_id:
                    bom_point = bom_obj.browse(cr, uid, bom_id)
                    routing_id = bom_point.routing_id.id or False
                    self.write(cr, uid, [production.id], {'bom_id': bom_id, 'routing_id': routing_id})

            if not bom_id:
                raise osv.except_osv(_('Error'), _("Couldn't find bill of material for product"))

            factor = uom_obj._compute_qty(cr, uid, production.product_uom.id, production.product_qty, bom_point.product_uom.id)
            res = bom_obj._bom_explode(cr, uid, bom_point, factor / bom_point.product_qty, properties)
            results = res[0]
            results2 = res[1]
            results3 = res[2]
            for key, value in results3.iteritems():
                #print key
                stock_journal = self.pool.get('stock.journal').browse(cr, uid, [key])
                if stock_journal:
                    seq_obj_name = stock_journal[0].sequence_id.code
                    picking_name = self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
                else:
                    raise osv.except_osv(_('Check Value !'), _('Sequence empty in Stock Journal'))
                #POP-002
                date_create = datetime.strptime(production.date_planned, '%Y-%m-%d %H:%M:%S') - relativedelta(days=production.product_id.product_tmpl_id.produce_delay or 0.0)
                #newdate = newdate - relativedelta(days=company.manufacturing_lead)

                picking = {
                    'name': picking_name,
                    'production_id': production.id,
                    'origin': (production.origin or '').split(':')[0] + ':' + production.name,
                    'stock_journal_id': key,        
                    'type': 'internal',            
                    'move_type': 'one',
                    'company_id': production.company_id.id,
                    'state': 'draft',
                    'min_date': production.date_planned,
                    'date': date_create.strftime('%Y-%m-%d %H:%M:%S'),
                }
                picking_id = stock_picking_obj.create(cr, uid, picking)
                production_location = production.product_id.product_tmpl_id.property_stock_production.id
                newdate = production.date_planned
                
                for data in value:
                    #POP-003
                    uom_id = self.pool.get('product.uom').browse(cr, uid, [data['product_uom']] )[0]
                    #print data
                    move_id = stock_move_obj.create(cr, uid, {
                        'name':'PROD:' + production.name,
                        'picking_id':picking_id,
                        'product_id': data['product_id'],
                        'product_qty': data['product_qty'],
                        'product_uom': data['product_uom'],
                        'product_uos_qty': data['product_qty'],
                        'product_uos': data['product_uom'],
                        'date': date_create.strftime('%Y-%m-%d %H:%M:%S'),
                        'location_id': production.location_src_id.id,
                        'location_dest_id': production_location,
                        'state': 'draft',
                        'company_id': production.company_id.id,
                        'date_expected': date_create.strftime('%Y-%m-%d %H:%M:%S'), #newdate,
                        'category_id': uom_id.category_id.id,
                    })
                    
            #raise osv.except_osv(_('Check Value !'), _('%s' % res[2]))                

            for line in results:
                line['production_id'] = production.id
                prod_line_obj.create(cr, uid, line)
            for line in results2:
                line['production_id'] = production.id
                workcenter_line_obj.create(cr, uid, line)
        return len(results)    

    def action_confirm(self, cr, uid, ids):
        """ Confirms production order.
        @return: Newly generated picking Id.
        """
        stock_picking_obj = self.pool.get("stock.picking")
        move_obj = self.pool.get('stock.move')
        for production in self.browse(cr, uid, ids):
            if not production.product_lines:
                self.action_compute(cr, uid, [production.id])
                production = self.browse(cr, uid, [production.id])[0]

            source = production.product_id.product_tmpl_id.property_stock_production.id
            if production.product_id.ineco_stock_journal_id:
                stock_journal = self.pool.get('stock.journal').browse(cr, uid, [production.product_id.ineco_stock_journal_id.id])
                if stock_journal:
                    seq_obj_name = stock_journal[0].sequence_id.code
                    picking_name = self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
                else:
                    raise osv.except_osv(_('Check Value !'), _('Sequence empty in Stock Journal'))
            else:
                raise osv.except_osv(_('Check Value !'), _('Stock Journal Empty in Product:'+production.product_id.name))
            
            #POP-002
            date_create = datetime.strptime(production.date_planned, '%Y-%m-%d %H:%M:%S') - relativedelta(days=production.product_id.product_tmpl_id.produce_delay or 0.0)
            #newdate = newdate - relativedelta(days=company.manufacturing_lead)
            
            picking = {
                'name': picking_name,
                'production_id': production.id,
                'origin': (production.origin or '').split(':')[0] + ':' + production.name,
                'stock_journal_id': production.product_id.ineco_stock_journal_id.id,        
                'type': 'internal',            
                'move_type': 'one',
                'company_id': production.company_id.id,
                'state': 'draft',
                'min_date': production.date_planned,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            picking_id = stock_picking_obj.create(cr, uid, picking)

            data = {
                'name':'PROD:' + production.name,
                'date': time.strftime('%Y-%m-%d %H:%M:%S'), #date_create.strftime('%Y-%m-%d %H:%M:%S'),
                'product_id': production.product_id.id,
                'product_qty': production.product_qty,
                'product_uom': production.product_uom.id,
                'product_uos_qty': production.product_uos and production.product_uos_qty or False,
                'product_uos': production.product_uos and production.product_uos.id or False,
                'location_id': source,
                'location_dest_id': production.location_dest_id.id,
                'move_dest_id': production.move_prod_id.id,
                'state': 'waiting',
                'company_id': production.company_id.id,
                'picking_id': picking_id,
                'date_expected': date_create.strftime('%Y-%m-%d %H:%M:%S'), #production.date_planned,
                'production_id': production.id,
            }
            res_final_id = move_obj.create(cr, uid, data)
            #self.write(cr, uid, [production.id], {'move_created_ids': [(6, 0, [res_final_id])]})
            self.write(cr, uid, [production.id], {'state':'ready'})
            
            message = _("Manufacturing order '%s' is scheduled for the %s.") % (
                production.name,
                datetime.strptime(production.date_planned,'%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y'),
            )
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'mrp.production',  production.id, 'button_produce', cr)
            self.log(cr, uid, production.id, message)
        return picking_id

    def copy(self, cr, uid, id, default={}, context=None, done_list=[], local=False):
        if not default:
            default = {}
        default = default.copy()
        default['ineco_stock_picking_ids'] = False
        default['date_planned'] = time.strftime('%Y-%m-%d %H:%M:%S')
        if not local:
            done_list = []
        return super(mrp_production, self).copy(cr, uid, id, default, context=context)

    def force_production(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state':'ready'})
        return True

    def do_production(self, cr, uid, ids, *args):
        for production in self.browse(cr, uid, ids):
            res = True
            for picking in production.ineco_stock_picking_ids:
                isOutput = False
                for move in picking.move_lines:
                    if move.product_id.id == production.product_id.id:
                        isOutput = True
                if not isOutput:
                    if picking.state not in ['done','cancel']:
                        res = False;
            if res:
                self.write(cr, uid, ids, {'state': 'in_production', 'date_start': time.strftime('%Y-%m-%d %H:%M:%S')})
            else:
                raise osv.except_osv(_('Warning!'), _('Some stock picking is not complete.'))
        return True


mrp_production()


class mrp_product_produce(osv.osv_memory):
    _inherit = "mrp.product.produce"
    _description = "Inherit Product Produce Wizard"

    def _get_product_qty(self, cr, uid, context=None):
        """ To obtain product quantity
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param context: A standard dictionary
        @return: Quantity
        """
        if context is None:
            context = {}
        prod = self.pool.get('mrp.production').browse(cr, uid,
                                context['active_id'], context=context)
        done = 0.0
        stock_move_ids = self.pool.get('stock.move').search(cr, uid, 
            [('product_id','=',prod.product_id.id),
             ('production_id','=',prod.id),
             ('state','in',['waiting'])])

        for move in self.pool.get('stock.move').browse(cr, uid,stock_move_ids) :
            done += move.product_qty
        return done 

    _defaults = {
         'product_qty': _get_product_qty,
         'mode': lambda *x: 'consume_produce'
    }

    def do_produce(self, cr, uid, ids, context=None):
        """ To check the product type
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: the ID or list of IDs if we want more than one
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        prod_obj = self.pool.get('mrp.production')
        move_ids = context.get('active_ids', [])
        for data in self.browse(cr, uid, ids, context=context):
            for move_id in move_ids:
                prod_obj.action_produce(cr, uid, move_id,
                                    data.product_qty, data.mode, context=context)
        return {'type':'ir.actions.act_window_close' }
    
mrp_product_produce()
