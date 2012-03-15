# -*- encoding: utf-8 -*-
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

import wizard
import pooler
from tools.translate import _

asset_ask_form = '''<?xml version="1.0"?>
<form string="Generate QRCode">
</form>'''

asset_ask_fields = {
}

def _asset_compute(self, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    asset_ids = pool.get('ineco.asset').search(cr, uid, [('image_url','=',None)])
    asset_obj = pool.get('ineco.asset').browse(cr, uid, asset_ids)
    for asset in asset_obj:
        pool.get('ineco.asset').generate_qrcode2(cr,uid,[asset.id])
    return {}

def _asset_open(self, cr, uid, data, context):
    value = {
        'name': 'Asset',
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'ineco.asset',
        'view_id': False,
        'type': 'ir.actions.act_window'
    }
    return value

def _get_period(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    ids = pool.get('account.period').find(cr, uid, context=context)
    period_id = False
    if len(ids):
        period_id = ids[0]
    return {'period_id': period_id}

class wizard_asset_qrcode(wizard.interface):
    states = {
        'init': {
            'actions': [_get_period],
            'result': {'type':'form', 'arch':asset_ask_form, 'fields':asset_ask_fields, 'state':[
                ('end','Cancel'),
                ('asset_compute','Generate Now!')
            ]}
        },
        'asset_compute': {
            'actions': [_asset_compute],
            'result': {'type':'action', 'action': _asset_open,  'state':'end'}
        }
    }
wizard_asset_qrcode('account.asset.qrcode')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

