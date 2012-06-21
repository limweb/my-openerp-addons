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

from datetime import datetime
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
                if bom.product_id.ineco_stock_journal_id:
                    result3[bom.product_id.ineco_stock_journal_id.id] = []
                    data = {
                        'product_id': bom.product_id.id,
                        'product_qty': bom.product_qty * factor,
                        'product_uom': bom.product_uom.id,
                    }
                    result3[bom.product_id.ineco_stock_journal_id.id] = [data]
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
    }
    
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
                print key
                stock_journal = self.pool.get('stock.journal').browse(cr, uid, [key])
                if stock_journal:
                    seq_obj_name = stock_journal[0].sequence_id.code
                    picking_name = self.pool.get('ir.sequence').get(cr, uid, seq_obj_name)
                else:
                    raise osv.except_osv(_('Check Value !'), _('Sequence empty in Stock Journal'))
                picking = {
                    'name': picking_name,
                    'production_id': production.id,
                    'origin': (production.origin or '').split(':')[0] + ':' + production.name,
                    'stock_journal_id': key,        
                    'type': 'internal',            
                    'move_type': 'one',
                    'company_id': production.company_id.id,
                    'state': 'draft',
                }
                picking_id = stock_picking_obj.create(cr, uid, picking)
                production_location = production.product_id.product_tmpl_id.property_stock_production.id
                newdate = production.date_planned
                for data in value:
                    print data
                    move_id = stock_move_obj.create(cr, uid, {
                        'name':'PROD:' + production.name,
                        'picking_id':picking_id,
                        'product_id': data['product_id'],
                        'product_qty': data['product_qty'],
                        'product_uom': data['product_uom'],
                        'product_uos_qty': data['product_qty'],
                        'product_uos': data['product_uom'],
                        'date': newdate,
                        'location_id': production.location_src_id.id,
                        'location_dest_id': production_location,
                        'state': 'waiting',
                        'company_id': production.company_id.id,
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
            
            picking = {
                'name': picking_name,
                'production_id': production.id,
                'origin': (production.origin or '').split(':')[0] + ':' + production.name,
                'stock_journal_id': production.product_id.ineco_stock_journal_id.id,        
                'type': 'internal',            
                'move_type': 'one',
                'company_id': production.company_id.id,
                'state': 'draft',
            }
            picking_id = stock_picking_obj.create(cr, uid, picking)

            data = {
                'name':'PROD:' + production.name,
                'date': production.date_planned,
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
            }
            res_final_id = move_obj.create(cr, uid, data)
            #self.write(cr, uid, [production.id], {'move_created_ids': [(6, 0, [res_final_id])]})
            self.write(cr, uid, [production.id], {'state':'ready'})
            
            message = _("Manufacturing order '%s' is scheduled for the %s.") % (
                production.name,
                datetime.strptime(production.date_planned,'%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y'),
            )
            self.log(cr, uid, production.id, message)
        return picking_id

mrp_production()
