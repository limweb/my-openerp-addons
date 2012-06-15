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

import wizard
from osv import osv
import pooler
from osv import fields
import time

def _launch_wizard(self, cr, uid, data, context=None):
    pool = pooler.get_pool(cr.dbname)

    #config_ids = pool.get('ineco.google.map').search(cr, uid, [])
    #config_obj = pool.get('ineco.google.map').browse(cr, uid, config_ids)[0]

    contact_obj= pooler.get_pool(cr.dbname).get('omg.sale.reserve.contact')
    m = contact_obj.browse(cr, uid, data['id'], context=context)
        
    apache_ids = pool.get('omg.configuration').search(cr, uid, [('type','=','apache')])
    hostname = 'localhost'
    path = '/py/booking'
    if apache_ids:
        apache_obj = pool.get('omg.configuration').browse(cr, uid, apache_ids)[0]
        hostname = apache_obj['host']
        path = apache_obj['url']
    
    if m.service_id.categ_id.ineco_check_place:
        check=1
    else:
        check=0
    if m.service_id.categ_id.ineco_check_categ:
        check_categ=1
    else:
        check_categ=0

    url=''
    url="http://"+hostname+path+"?id="+str(m.id)+"&product_id="+str(m.product_id.id)+"&category_id="+str(m.product_id.categ_id.id)+"&sale_id="+str(m.saleman_id.id)+"&dbname="+cr.dbname+"&sevice_category_id="+str(m.service_id.categ_id.id)+"&check="+str(check)+"&check_cate="+str(check_categ)
    #+"&uid="+str(config_obj.username)+"&pwd="+str(config_obj.password)+"&dbname="+str(config_obj.dbname)+"&host="+str(config_obj.hostname)
#    url="http://www.google.com"
    return {
        'type': 'ir.actions.act_url',
        'url':url,
        'nodestroy': True,
        'target': 'new'
    }

class launch_map(wizard.interface):

    states= {'init' : {'actions': [],
                       'result':{'type':'action',
                                 'action': _launch_wizard,
                                 'state':'end'}
                       }
             }
launch_map('search_all_launch')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

