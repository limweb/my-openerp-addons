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

#
# 30-01-2012    POP-001        Add Note Field in mrp.production.
# 13-02-2012    POP-002        Add Delivery Date in Production.

from datetime import datetime
from osv import osv, fields
from tools.translate import _
import netsvc
import time
import tools
import os
from PyQRNative import *
import urllib

image_level = 5

class ineco_mrp_production_tracking(osv.osv):

    def _get_date_planned(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            date_planned = False
            last_planned = False
            for workcenter in line.tracking_lines:
                if not workcenter.date_finished and not date_planned:
                    date_planned = workcenter.date_planned
                last_planned = workcenter.date_planned
            res[line.id] = date_planned or last_planned
        return res

    def _get_date_finished(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            date_finished = False
            for workcenter in line.tracking_lines:
                date_finished = workcenter.date_finished
            res[line.id] = date_finished
        return res
    
    def _get_next_workcenter(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            next_workcenter = ""
            for workcenter in line.tracking_lines:
                if not next_workcenter:    
                    if not workcenter.date_finished:
                        next_workcenter = workcenter.workcenter_id.name
            res[line.id] = next_workcenter
        return res
    
    def _progress_rate(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for line in self.browse(cursor, user, ids, context=context):
            complete_qty = 0
            max_qty = len(line.tracking_lines)
            #print max_qty
            for workcenter in line.tracking_lines:
                if workcenter.date_finished:
                    complete_qty += 1
            res[line.id] = min(100.0, complete_qty * 100 / (max_qty or 1.00))
        return res

    
    _name = "ineco.mrp.production.tracking"
    _description = "Tracking production in production line"
    _orderby = 'production_id, sequence'
    _columns = {
        'name': fields.char('Description',size=250,required=True),
        'production_id': fields.many2one('mrp.production','Production Order',ondelete='cascade',required=True),
        'product_id': fields.many2one('product.product','Product',required=True, ondelete='restrict'),
        'origin': fields.char('Origin', size=100),
        'uom_id': fields.many2one('product.uom','UOM',required=True, ondelete='restrict'),
        'sequence': fields.integer('Sequence'),
        'date_planned': fields.function(_get_date_planned, method=True, string="Date Planned", type="datetime"),
        'date_finished': fields.function(_get_date_finished, method=True, string="Date Finished", type="datetime"),
        'workcenter_id': fields.function(_get_next_workcenter, method=True, string='Next Workcenter', type='string'),
        'tracking_lines': fields.one2many('ineco.mrp.production.tracking.line','tracking_id','Tracking Lines'),
        'progress_rate': fields.function(_progress_rate, method=True, string="Progress", type="float"),
        'image_url': fields.char('Image URL', size=240),
        'note': fields.char('Note', size=100),
        'date_target': fields.date('Sale Target Date'),
        'date_delivery': fields.date('Delivery Date'),
    }
    _defaults = {
        'name': '/',
    }
        
    def create(self, cr, uid, vals, context=None):
        id = super(ineco_mrp_production_tracking, self).create(cr, uid, vals, context)

        dir = "/var/www/images/"+self._name
        if not os.path.exists(dir):
            os.makedirs(dir)
        image_url = ""
        qr = QRCode(image_level, QRErrorCorrectLevel.L)
        data = []
        data.append(self._name)
        data.append(str(id))
        qr.addData('tracking:'+str(id)+':'+self._name)
        qr.make()
        
        #import ast
        #ast.literal_eval(str(data))
        
        im = qr.makeImage()
        im.save(dir+'/'+str(id),'png')
        
        image_url = "http://localhost/images/"+self._name+"/"+str(id)
        super(ineco_mrp_production_tracking, self).write(cr, uid, id, {'image_url':image_url})
        
        return id
    
    def gen_qrcode(self, cr, uid, ids, context=None):
        
        for tracking in self.browse(cr, uid, ids):
        
            dir = "/var/www/images/"+self._name
            if not os.path.exists(dir):
                os.makedirs(dir)
                
            image_url = ""
            qr = QRCode(image_level, QRErrorCorrectLevel.L)
            data = []
            data.append(self._name)
            data.append(str(tracking.id))
            qr.addData('tracking:'+str(tracking.id)+':'+self._name)
            qr.make()
            
            im = qr.makeImage()
            im.save(dir+'/'+str(tracking.id),'png')
            
            image_url = "http://localhost/images/"+self._name+"/"+str(tracking.id)
            tracking.write({'image_url': image_url})

        return True

    def unlink(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        dir = "/var/www/images/"+self._name+'/'+str(id)+'.png'
        os.remove(dir)       
        return super(ineco_mrp_production_tracking, self).write(cr, uid, ids, vals, context=context)
    
    def act_done(self, cr, uid, ids, context=None):
        prod_obj = self.pool.get('mrp.production')
        for tracking in self.browse(cr, uid, ids):
            for production in self.pool.get('mrp.production').browse(cr, uid, [tracking.production_id.id] ):
                prod_obj.action_produce(cr, uid, production.id, production.product_qty, "consume_produce", context)
            print "Production Done"
        return True

ineco_mrp_production_tracking()

class ineco_mrp_production_tracking_line(osv.osv):
    _name = "ineco.mrp.production.tracking.line"
    _description = "Tracking production in production line"
    _orderby = 'tracking_id, sequence'
    _columns = {
        'name': fields.char('Description',size=250,required=True),
        'tracking_id': fields.many2one('ineco.mrp.production.tracking','Tracking',ondelete='cascade',required=True),
        'product_id': fields.many2one('product.product','Product',required=True, ondelete='restrict'),
        'uom_id': fields.many2one('product.uom','UOM',required=True, ondelete='restrict'),
        'workcenter_id': fields.many2one('mrp.workcenter','Workcenter',required=True, ondelete='restrict'),
        'sequence': fields.integer('Sequence'),
        'date_planned': fields.datetime('Date Planned'),
        'date_finished': fields.datetime('Date Finished'),
        'user_id': fields.many2one('res.users', 'User', readondate_finishedly=True, ondelete='restrict'),
        'state': fields.selection([('draft','Open'), ('done','Done'),('cancel','Cancel')], 'State', readonly=True),
        'image_url': fields.char('Image URL', size=240),
    }
    _defaults = {
        'name': '/',
        'user_id': lambda s, cr, u, c: u,
        'state': 'draft'
    }
    
    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'done','date_finished':time.strftime('%Y-%m-%d %H:%M:%S')})
        for line in self.browse(cr, uid, ids):
            for track in self.pool.get('ineco.mrp.production.tracking').browse(cr, uid, [line.tracking_id.id] ):
                print track.name, track.progress_rate
        return True
    
    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft','date_finished':False})
        return True 
    
    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'cancel','date_finished': False})
        return True 

    def create(self, cr, uid, vals, context=None):
        id = super(ineco_mrp_production_tracking_line, self).create(cr, uid, vals, context)

        dir = "/var/www/images/"+self._name
        if not os.path.exists(dir):
            os.makedirs(dir)
        image_url = ""
        qr = QRCode(image_level, QRErrorCorrectLevel.L)
        data = []
        data.append(self._name)
        data.append(str(id))
        qr.addData('tracking:'+str(id)+':'+self._name)
        qr.make()
        
        #import ast
        #ast.literal_eval(str(data))
        
        im = qr.makeImage()
        im.save(dir+'/'+str(id),'png')
        
        image_url = dir+"/"+str(id)+".png"
        super(ineco_mrp_production_tracking_line, self).write(cr, uid, id, {'image_url':image_url})
        
        return id
    
    def unlink(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        dir = "/var/www/images/"+self._name+'/'+str(id)+'.png'
        os.remove(dir)       
        return super(ineco_mrp_production_tracking_line, self).write(cr, uid, ids, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if ('date_finished' in vals):
            if vals.get('date_finished'):           
                all_complete_qty = 0      
                for line in self.browse(cr, uid, ids):
                    complete_qty = 0
                    for track in self.pool.get('ineco.mrp.production.tracking').browse(cr, uid, [line.tracking_id.id] ):
                        max_qty = len(track.tracking_lines)
                        prod_id = track.production_id.id
                        for workcenter in track.tracking_lines:
                            if workcenter.id == line.id:
                                complete_qty += 1
                            if workcenter.date_finished:
                                complete_qty += 1
                        percent = min(100.0, complete_qty * 100 / (max_qty or 1.00))
                        if percent >= 99.99:
                            all_complete_qty += 1
                    for production in self.pool.get('mrp.production').browse(cr, uid, [prod_id] ):
                        max_prod_qty = len(production.tracking_lines)
                        for track in production.tracking_lines:
                            if track.progress_rate >= 99.99:
                                all_complete_qty += 1
                    track_percent = min(100.0, all_complete_qty * 100 / (max_prod_qty or 1.00))
                    if track_percent >= 99.99:
                         track.act_done()
        return super(ineco_mrp_production_tracking_line, self).write(cr, uid, ids, vals, context)   
    
ineco_mrp_production_tracking_line()

class mrp_production(osv.osv):
    _name = "mrp.production"
    _inherit = "mrp.production"
    _description = "Generate Tracking Product"

    _columns = {
        'tracking_lines': fields.one2many('ineco.mrp.production.tracking','production_id','Tracking Lines'),
        'partner_id': fields.many2one('res.partner', 'Customer', ondelete="restrict"),
        'sr_width': fields.float('Width', digits=(10,2)),
        'sr_length': fields.float('Length', digits=(10,2)),
        'sale_target_date': fields.date('Sale Target Date'),
        #POP-002
        'delivery_date': fields.date('Delivery Date'),
        #POP-001
        'note': fields.char('Note', size=100),
        'sale_line_id': fields.many2one('sale.order.line', 'Sale Line'),
    }

    def action_compute(self, cr, uid, ids, properties=[]):
        result = super(mrp_production, self).action_compute(cr, uid, ids)
        for po in self.browse(cr, uid, ids):
            cr.execute( ("delete from ineco_mrp_production_tracking where production_id = %d " % po.id) )
            qty = 1 
            context = {}
            product_name = self.pool.get('product.product').name_get(cr, uid, [po.product_id.id], context=context)[0][1]
            while qty <= int(po.product_qty):
                tracking_id = self.pool.get('ineco.mrp.production.tracking').create(cr, uid,  {
                    'name': 'Seq '+str(qty)+'. '+po.origin+'-'+product_name,
                    'production_id': po.id,
                    'origin': po.origin, 
                    'product_id': po.product_id.id,
                    'uom_id': po.product_id.uom_id.id,
                    'sequence': qty,
                    'date_planned': po.date_planned,
                    'note': po.note,
                    'date_target': po.sale_target_date,
                    'date_delivery': po.delivery_date,
                })                
                for wcl in po.workcenter_lines:
                    found_ids = self.pool.get('ineco.mrp.production.tracking.line').search(cr, uid, [('tracking_id','=',tracking_id),('workcenter_id','=',wcl.workcenter_id.id)])
                    if not found_ids:
                        tracking_line_id = self.pool.get('ineco.mrp.production.tracking.line').create(cr, uid,  {
                            'name': 'Seq '+str(qty)+'. '+po.origin+'-'+product_name,
                            'tracking_id': tracking_id,
                            'product_id': po.product_id.id,
                            'uom_id': po.product_id.uom_id.id,
                            'workcenter_id': wcl.workcenter_id.id,
                            'sequence': wcl.sequence,
                            'date_planned': wcl.date_planned,
                        })
                qty += 1
        return result 

mrp_production()

class mrp_bom(osv.osv):
    
    _name = "mrp.bom"
    _inherit = "mrp.bom"
    _description = "Change Default Routing"
    
    _columns = {
        'double_qty': fields.boolean('Double Quantity'),
    }
    
    def onchange_product_id(self, cr, uid, ids, product_id, name, context=None):
        """ Changes UoM and name if product_id changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            v = {'product_uom': prod.uom_id.id}
            if not name:
                v['name'] = prod.name
            bom_ids = self.pool.get('mrp.bom').search(cr, uid, [('product_id','=',product_id),('bom_id','=',False)])
            if bom_ids:
                bom = self.pool.get('mrp.bom').browse(cr, uid, bom_ids[0])
                if bom.routing_id:
                    v['routing_id'] = bom.routing_id.id
            return {'value': v}
        return {}

mrp_bom()

class ineco_mrp_production_tracking_fixed(osv.osv):
    
    def _get_product(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.tracking_id.product_id.name or ""
        return res

    def _get_origin(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.tracking_id.origin or ""
        return res
    
    _name = "ineco.mrp.production.tracking.fixed"
    _description = "Fix Tracking"
    _columns = {
        'name': fields.char('Description',size=250,required=True),
        'date_planned': fields.datetime('Date Fixed'),
        'workcenter_id': fields.many2one('mrp.workcenter','Workcenter',required=True, ondelete='restrict'),
        'tracking_id': fields.many2one('ineco.mrp.production.tracking','Tracking',ondelete='cascade',required=True),
        'user_id': fields.many2one('res.users', 'User', readondate_finishedly=True, ondelete='restrict'),
        'product_id': fields.function(_get_product, method=True, string="Product", type="string"),
        'origin': fields.function(_get_origin, method=True, string="Origin", type="string"),
    }
    _defaults = {
        'user_id': lambda s, cr, u, c: u,
        'date_planned': time.strftime('%Y-%m-%d %H:%M:%S'),
    }

ineco_mrp_production_tracking_fixed()
