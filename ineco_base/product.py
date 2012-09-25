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

# Date             ID         Message
# 31-12-2011       POP-001    Make sure for Warehouse_UOM already in new product record.
# 09-02-2012       POP-002    Change path to store image of product.

import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp
import base64
import os
import Image
import urllib

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class ineco_stock_sticker(osv.osv):
    _name = "ineco.stock.sticker.category"
    _description = "Warehouse Delivery Sticker" 
    _columns = {
        'name': fields.char('Sticker Category', size=50, required=True),
        'printable': fields.boolean('Printable'),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'printable': True,
        'active': True,
    }
ineco_stock_sticker()

class ineco_stock_keeping_method(osv.osv):
    
    def _get_location_count(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        sql = "select count(*) as total from stock_location where keeping_id = %s"
        for each in ids:
            cr.execute(sql % (each))
            count =  cr.dictfetchall()
            res[each] = count[0]['total']
        return res

    def _get_location_available(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        sql = """ 
                select 
                  iskm.id,
                  (select count(*) from stock_location where stock_location.keeping_id = iskm.id) as total,
                  sum(case abs( (select count(*) from stock_move sm1 where sm1.location_dest_id = sl.id) -
                    (select count(*) from stock_move sm1 where sm1.location_id = sl.id) )
                    when 0 then 0
                    else 1 
                  end) as already,
                  (select count(*) from stock_location where stock_location.keeping_id = iskm.id) - 
                  sum(case abs( (select count(*) from stock_move sm1 where sm1.location_dest_id = sl.id) -
                    (select count(*) from stock_move sm1 where sm1.location_id = sl.id) )
                    when 0 then 0
                    else 1 
                  end) as available
                from
                  ineco_stock_keeping_method iskm
                left join stock_location sl on iskm.id = sl.keeping_id
                where iskm.id = %s
                group by iskm.id, total
        """
        for each in ids:
            cr.execute(sql % (each))
            count =  cr.dictfetchall()
            res[each] = count[0]['available']
        return res
    
    _name = "ineco.stock.keeping.method"
    _description = "Method for keeping wizard location."
    _columns = {
        'name': fields.char('Name', size=128, required=True),
        'total_location': fields.function(_get_location_count, string="Location Count", type="integer", method=True),
        'available_location': fields.function(_get_location_available, string="Available", type="integer", method=True),
        'location_ids': fields.one2many('stock.location','keeping_id','Locations'),
        'active': fields.boolean('Active')
    }
    _defaults = {
        'active': True
    }
ineco_stock_keeping_method()


class product_uom_categ(osv.osv):
    _name = 'product.uom.categ'
    _inherit = 'product.uom.categ'
    _description = 'Product uom categ'
    _columns = {
        'line_ids': fields.one2many('product.uom','category_id','UOM Lines'),
    }

product_uom_categ()

class product_product(osv.osv):

    def get_image(self, cr, uid, id):
        each = self.read(cr, uid, id, ['image_garment'])
        img = each['image_garment']
        return img

    def get_image_url(self, cr, uid, id):
        image_path = self.read(cr, uid, id, ['image_url'])
        image = False
        if image_path['image_url'] and os.path.exists(image_path['image_url']) and os.path.isfile(image_path['image_url']):
            image = base64.encodestring(open(image_path['image_url'],"rb").read())
        return image

    def _get_image(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for each in ids:
            res[each] = self.get_image_url(cr, uid, each)
        return res

    def get_image_attachment_url(self, cr, uid, ids, url):
        image = False
        if url :
            try:
                if url.find('.jpg') or url.find('.bmp') or url.find('.gif'):
                    tmp = urllib.urlopen(url).read()
                    if tmp:
                        image = base64.encodestring(tmp) 
            except:
                pass
            #image = base64.encodestring(Image.open(StringIO(urllib.urlopen(url).read())))
        return image

    def _get_image_attachment(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        attach_ids = self.pool.get('ir.attachment').search(cr, uid, [('type','=','url'),('res_model','=','product.product'),('res_id','in',ids)])
        index = 0
        for each in ids:
            for attach in self.pool.get('ir.attachment').browse(cr, uid, attach_ids) :
                index += 1
                if index == 1 :
                     res[each] = self.get_image_attachment_url(cr, uid, ids, attach.url)
        return res

    def _get_image_attachment2(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        attach_ids = self.pool.get('ir.attachment').search(cr, uid, [('type','=','url'),('res_model','=','product.product'),('res_id','in',ids)])
        index = 0
        for each in ids:
            if attach_ids and len(attach_ids) >= 2: 
                attach = self.pool.get('ir.attachment').browse(cr, uid, attach_ids)[1]
                res[each] = self.get_image_attachment_url(cr, uid, ids, attach.url)
                     
        return res

    def _get_image_attachment3(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        attach_ids = self.pool.get('ir.attachment').search(cr, uid, [('type','=','url'),('res_model','=','product.product'),('res_id','in',ids)])
        index = 0
        for each in ids:
            for attach in self.pool.get('ir.attachment').browse(cr, uid, attach_ids) :
                index += 1
                if index == 3 :
                     res[each] = self.get_image_attachment_url(cr, uid, ids, attach.url)
        return res
    
    _name = "product.product"
    _inherit = "product.product"
    _description = "Image of product"
    _columns = {        
        'image_garment':fields.binary('Image', filters='*.jpg'),
        'preview_image_garment':fields.function(_get_image, type="binary", method=True),
        'image_url': fields.char('Image URL', size=240),
        'keeping_id': fields.many2one('ineco.stock.keeping.method','Keeping Method'),
        'warehouse_uom': fields.many2one('product.uom', 'Warehouse Unit of Measure'),
        'sticker_category_id': fields.many2one('ineco.stock.sticker.category', 'Sticker Category'),
        'attachment_image1': fields.function(_get_image_attachment, type="binary", method=True),
        'attachment_image2': fields.function(_get_image_attachment2, type="binary", method=True),
        'attachment_image3': fields.function(_get_image_attachment3, type="binary", method=True),
    }

    #POP-001
    def onchange_uom(self, cursor, user, ids, uom_id,uom_po_id):
        if uom_id and uom_po_id:
            uom_obj=self.pool.get('product.uom')
            uom=uom_obj.browse(cursor,user,[uom_id])[0]
            uom_po=uom_obj.browse(cursor,user,[uom_po_id])[0]
            if uom.category_id.id != uom_po.category_id.id:
                return {'value': {'uom_po_id': uom_id}}
        if uom_id or uom_po_id:
            id_uom = uom_id or uom_po_id
            uom_obj = self.pool.get('product.uom').browse(cursor, user, [id_uom])[0]
            uom_categ_id = uom_obj.category_id.id 
            uom_categ = self.pool.get('product.uom').search(cursor, user, [('category_id','=',uom_categ_id)])
            if uom_categ:
                warehouse_uom_id = False
                min_factor = 10
                for uom in self.pool.get('product.uom').browse(cursor, user, uom_categ):
                    if uom.factor < min_factor:
                        warehouse_uom_id = uom.id
                        min_factor = uom.factor
                return {'value': {'warehouse_uom': warehouse_uom_id}}
        return False

    def schedule_export_image(self, cr, uid, context=None):
        if context is None:
            context = {}
        product_ids = self.pool.get('product.product').search(cr, uid, [('image_garment','<>',False)])
        if product_ids:
            for product in self.pool.get('product.product').browse(cr, uid, product_ids):
                if product.image_garment:
                    dir = "/var/www/images/"+cr.dbname+"/"+self._name
                    if not os.path.exists(dir):
                        os.makedirs(dir)
                    image_url = ""
                    buf = StringIO()
                    buf.write(product.image_garment)
                    try:
                        file = open (dir+"/"+str(product.id)+".jpg","wb")
                        file.write(base64.decodestring(buf.getvalue()))
                        image_url = dir+"/"+str(product.id)+".jpg"
                        #product.write({'image_url': image_url,'image_garment':False})
                    except:
                        image_url = ""
                    else:
                        file.close()
                        buf.close()
                        product.write({'image_url': image_url,'image_garment':False})
        return True
    
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        #POP-002
        dir = "/var/www/images/"+cr.dbname+"/"+self._name
        if not os.path.exists(dir):
            os.makedirs(dir)
        image_url = ""
        if 'image_garment' in vals:
            if vals['image_garment'] != False:
                buf = StringIO()
                buf.write(vals['image_garment'])
                file = open (dir+"/"+str(ids[0])+".jpg","wb")
                file.write(base64.decodestring(buf.getvalue()))
                file.close()
                buf.close() 
                image_url = dir+"/"+str(ids[0])+".jpg"
                vals['image_url'] = image_url
                vals['image_garment'] = False
        return super(product_product, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        return super(product_product, self).unlink(cr, uid, ids, context=context)

product_product()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

