# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
import netsvc

import decimal_precision as dp

from osv import fields,osv
from tools.translate import _

import os
import sys
import math
from pygooglechart import QRChart
import base64

from PyQRNative import *
import urllib
import urllib2

ROOT = os.path.dirname(os.path.abspath(__file__))+'/images/'
sys.path.insert(0, os.path.join(ROOT, '..'))

class ineco_asset_type(osv.osv):
    
    _name =  "ineco.asset.type" 
    _description = "Type of asset."
    _columns = {
        'name': fields.char('Description', size=128, required=True),
        'active': fields.boolean('Active'),
    }
    
    _defaults = {
        'active': True,
    }
    
    _sql_constraints = [
        ('ineco_asset_type_unique', 'unique (name)', 'The type must be unique!'),
    ]
    
    def copy(self, cr, uid, id, default={}, context={}):
        name = self.read(cr, uid, [id], ['name'])[0]['name']
        default.update({'name': name+ _(' (copy)')})
        return super(ineco_asset_type, self).copy(cr, uid, id, default, context)
    
ineco_asset_type()

class ineco_asset(osv.osv):

    def _get_depreciation_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            dep_value = 0
            for depreciation in line.depreciation_ids:
                dep_value = dep_value + depreciation.depreciation
            res[line.id] = line.price_unit - dep_value
        return res

    def _get_last_location(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            last_location = ""
            for history in line.history_ids:
                if last_location:    
                    last_location = last_location               
                else:
                    last_location = history.location_to.name
            res[line.id] = last_location
        return res

    def _get_last_owner(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            last_owner = ""
            for history in line.history_ids:
                if last_owner:    
                    last_owner = last_owner               
                else:
                    last_owner = history.owner_to.name
            res[line.id] = last_owner
        return res

    def _get_image(self, cr, uid, ids, field_name, arg, context):
        ret = {}
        if context is None:
            context = {}
        image_path = ''
        for line in self.browse(cr, uid, ids, context=context):
            if line.image_url:
                image_path = line.image_url
                picture_res = urllib2.urlopen(image_path)
                picture = picture_res.read()
                basestr = base64.encodestring(picture)
                ret [line.id] = basestr
        return ret

    _name = "ineco.asset"
    _description = "Asset Master"
    _order = 'name'

    _columns = {
        'name':fields.char('Asset ID', size=32, select=True, required=True),
        'register_date':fields.datetime("Register Date", select=True, required=True),
        'product_id' : fields.many2one('product.product', 'Product', required=True, ondelete='restrict'),
        'partner_id' : fields.many2one('res.partner', 'Partner', required=True, ondelete='restrict'),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Sale Price')),
        'company_id': fields.many2one('res.company', 'Company', select=True, ondelete='restrict'),
        'location_id': fields.function(_get_last_location, method=True, string='Location', type='string'),
        'notes':fields.text("Notes"),
        'owner_id': fields.function(_get_last_owner, method=True, string='Owner', type='string'),
        'method': fields.selection([('linear', 'Linear'),
                                   ('declining', 'Declining'),
                                   ('manual', 'Manual')], 'Method',
                                   required=True),
        'percent': fields.float('Percent', required=True, digits_compute= dp.get_precision('Sale Price')),
        'history_ids': fields.one2many('ineco.asset.history', 'asset_id', 'Histories'),
        'depreciation_ids': fields.one2many('ineco.asset.depreciation', 'asset_id', 'Depreciation'),
        'depreciation_value': fields.function(_get_depreciation_value, method=True, string='Depreciation Value', digits_compute=dp.get_precision('Account'), type='float'),
        'period_id': fields.many2one('account.period', 'Start Period', ondelete='restrict'),
        'qrcode': fields.binary('QR Code', filters='*.png, *.gif, *.jpg'),
        'image_url': fields.char('Image URL', size=240),
        'image_path': fields.char('Image Path', size=240),
        "image": fields.function(_get_image, string="Image", type="binary", method=True),
        'asset_type_id': fields.many2one('ineco.asset.type', 'Asset Type'),
    }

    _defaults = {
        'method': 'linear',
        'percent': 5,
    }

    _sql_constraints = [
        ('name_asset_uniq', 'unique (name)', 'Asset code must be unique !')
    ]

    def create(self, cr, user, vals, context=None):
        if not vals['period_id']:
            period_ids = self.pool.get('account.period').search(cr, user, [('date_start','<=',vals['register_date'] or time.strftime('%Y-%m-%d')),('date_stop','>=',vals['register_date'] or time.strftime('%Y-%m-%d'))])
            if period_ids:
                period_id = period_ids[0]
            vals['period_id'] = period_id
        return super(ineco_asset,self).create(cr, user, vals, context)

    def generate_qrcode(self, cr, uid, ids, context=None):
        asset_ids = self.pool.get('ineco.asset').browse(cr, uid, ids)
        for asset in asset_ids:
            chart = QRChart(500, 500)            
            chart.add_data( u'รหัส: '+asset.name+'\n'+u'ชื่อ: '+asset.product_id.name_template+'\n'+u'วันลงทะเบียน: '+asset.register_date+'\n'+u'ผู้ขาย: '+asset.partner_id.name )
            chart.set_ec('H', 0)
            chart.download(ROOT+asset.name+'.png')            
            fd = open (ROOT+asset.name+'.png', "rb")
            if fd:
                qrcode_str = fd.read ()
                basestr = base64.encodestring(qrcode_str)
                asset.write({'qrcode': basestr})       
        return True
    
    def generate_qrcode2(self, cr, uid, ids, context=None):
        asset_ids = self.pool.get('ineco.asset').browse(cr, uid, ids)
        for asset in asset_ids:
            dir = "/var/www/images/"+self._name
            if not os.path.exists(dir):
                os.makedirs(dir)
            image_url = ""
            data = u'ID: '+asset.name+'\n'+u'Name: '+asset.product_id.name_template+'\n'+u'Supplier: '+asset.partner_id.name+'\n'+u'Register Date: '+ time.strftime('%B, %Y',time.strptime(asset.register_date,'%Y-%m-%d %H:%M:%S'))
            qr = QRCode(10, QRErrorCorrectLevel.L)
            qr.addData(data.encode('utf-8'))
            qr.make()
                
            im = qr.makeImage()
            im.save(dir+"/"+asset.name,'png')
            
            image_url = "http://localhost/images/"+self._name+"/"+asset.name
            image_path = dir+"/"+asset.name+'.png'
            asset.write({'image_url': image_url,'image_path':image_path})
    
ineco_asset()

class ineco_asset_history(osv.osv):
    _name = "ineco.asset.history"
    _description = "History Line of Asset"
    _order = "transaction_date desc"

    _columns = {
        'asset_id': fields.many2one("ineco.asset", "Asset", ondelete='restrict'),
        'transaction_date': fields.date("Transaction Date", required=True),
        'location_to': fields.many2one("hr.department","To Location", required=True, ondelete='restrict'),
#        'location_to': fields.many2one("stock.location","To Location", required=True, ondelete='restrict'),
        'owner_to': fields.many2one("res.users","To Owner", required=True, ondelete='restrict'),
        'user_id': fields.many2one("res.users","Recorder", required=True, ondelete='restrict'),
    }

    _defaults = {
        'transaction_date': lambda *a: time.strftime('%Y-%m-%d'),
        'user_id': lambda self, cr, uid, context: uid,
    }

ineco_asset_history()


class ineco_asset_depreciation(osv.osv):

    def _amount_compute(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.base_amount - line.depreciation
        return res

    _name = "ineco.asset.depreciation"
    _description = "Depreciation of Asset"
    _order = "period_id desc"

    _columns = {
        'asset_id': fields.many2one('ineco.asset', 'Asset', ondelete='restrict'),
        'period_id': fields.many2one('account.period', 'Period', required=True, ondelete='restrict'),
        'base_amount': fields.float('Base Amount', required=True, digits_compute= dp.get_precision('Account'), type='float'),
        'depreciation': fields.float('Depreciation', required=True, digits_compute= dp.get_precision('Account'), type='float'),
        'balance': fields.function(_amount_compute, method=True, string='Balance', digits_compute=dp.get_precision('Account'), type='float'),
    }

    _defaults = {
        'base_amount': 0,
        'depreciation': 0,
    }

    def create(self, cr, user, vals, context=None):
        if ('asset_id' in vals) :
            asset_ids = self.pool.get('ineco.asset').search(cr, user, [('id','=',vals['asset_id'])])
            if asset_ids:
                asset_obj = self.pool.get('ineco.asset').browse(cr, user, asset_ids)[0]
                if asset_obj:
                    base_amount = asset_obj.depreciation_value
                    vals['base_amount'] = base_amount
                    if asset_obj.method == "linear":
                        vals['depreciation'] = asset_obj.price_unit * asset_obj.percent / 100
                    elif asset_obj.method == "declining":
                        vals['depreciation'] = base_amount * asset_obj.percent / 100
                    if vals['depreciation'] > base_amount:
                        vals['depreciation'] = base_amount
        return super(ineco_asset_depreciation,self).create(cr, user, vals, context)

ineco_asset_depreciation()




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
