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

import os
import socket
import sys
import time
import netsvc
import decimal_precision as dp
from osv import fields,osv
from tools.translate import _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

import re
import tools
import base64
import random

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO 

class ineco_ir_attachment_configuration(osv.osv):
    _name = "ineco.ir.attachment.configuration"
    _description = "Configuration for Ineco Attachment"
    _columns = {
        'name': fields.char('Folder Path', size=254, required=True, help="example: /var/www/images/"),
        'url_template': fields.char('URL Template', size=254, required=True, help="http://localhost/images/"),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'name': '/var/www/images/',
        'url_template': 'http://localhost/images/',
        'active': True,
    }
ineco_ir_attachment_configuration()

class ineco_ir_attachment(osv.osv):
    
    _name = "ineco.ir.attachment"
    _description = "Ineco Attachment Utility."
    
    def schedule_attachment(self, cr, uid, context=None):
        config_ids = self.pool.get('ineco.ir.attachment.configuration').search(cr, uid, [])
        if config_ids:
            config = self.pool.get('ineco.ir.attachment.configuration').browse(cr, uid, config_ids)[0]
            if config:
                attach_ids = self.pool.get('ir.attachment').search(cr, uid, [('type','=','binary')])
                attach_obj = self.pool.get('ir.attachment').browse(cr, uid, attach_ids)
                for attach in attach_obj:
                    dir = config.name+self._name+'/'+str(attach.id)
                    if not os.path.exists(dir):
                        os.makedirs(dir)
                    image_url = config.url_template+self._name+'/'+str(attach.id)+"/"+attach.name
                    image_path = dir+'/'+attach.name
                    buf = StringIO()
                    buf.write(attach.datas)
                    file = open (image_path,"wb")
                    file.write(base64.decodestring(buf.getvalue()))
                    file.close()
                    buf.close() 
                    attach.write({'url': image_url,'datas':False,'type':'url'})
        return True
    
ineco_ir_attachment()

class ir_attachment(osv.osv):
    
    _name = "ir.attachment"
    _inherit = 'ir.attachment'
    _description = "Ineco Attachment."
    
    def create(self, cr, uid, vals, context=None):
        if ('datas' in vals):
            config_ids = self.pool.get('ineco.ir.attachment.configuration').search(cr, uid, [])
            if config_ids:
                config = self.pool.get('ineco.ir.attachment.configuration').browse(cr, uid, config_ids)[0]
                if config:
                    datas = vals.get('datas')
                    res_id = str(random.randint(10910929,18299919))
                    res_name = vals.get('name')
                    
                    dir = config.name+self._name+'/'+res_id
                    if not os.path.exists(dir):
                        os.makedirs(dir)
                    image_url = config.url_template+self._name+'/'+res_id+"/"+res_name
                    image_path = dir+'/'+res_name
                    buf = StringIO()
                    buf.write(datas)
                    file = open (image_path,"wb")
                    file.write(base64.decodestring(buf.getvalue()))
                    file.close()
                    buf.close() 
                    
                    vals['datas'] = False
                    vals['type'] = 'url'
                    vals['url'] = image_url
                    
        #self.check(cr, uid, ids, 'write', context=context, values=vals)
        return super(ir_attachment, self).create(cr, uid, vals, context)

ir_attachment()