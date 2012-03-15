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

import wizard
import netsvc
import tools
from osv import fields, osv
import socket 

class partner_sms_send(osv.osv_memory):
    """ Create Menu """

    _name = "partner.sms.send"
    _inherit = "partner.sms.send"
    _description = "Send SMS"

    _columns = {
    }
    
    def sms_send_by_thaibulksms(self, cr, uid, ids, context, mobile_to, text, sender_name='SMS', schedule='', force='standard'):
        import urllib
        host_ids = self.pool.get('omg.configuration').search(cr, uid, [('type','=','sms')])
        #url = "http://www.thaibulksms.com/sms_api.php"
        if host_ids:
            host_obj = self.pool.get('omg.configuration').browse(cr, uid, host_ids)[0]
            url = host_obj['host']
                
        params = urllib.urlencode({'username': user, 'password': password, 'msisdn': mobile_to,
                                   'message': tools.ustr(text),
                                   'sender': sender_name, 'ScheduledDelivery':schedule,'force':force})
        f = urllib.urlopen(url+"?"+params)
        return True

    def default_get(self, cr, uid, fields, context=None):
        partner_pool = self.pool.get('res.partner')
        active_ids = context and context.get('active_ids', [])
        res = {}
        for partner in partner_pool.browse(cr, uid, active_ids, context=context):            
            if 'mobile_to' in fields:
                res.update({'mobile_to': partner.mobile})          
                
        host_ids = self.pool.get('omg.configuration').search(cr, uid, [('type','=','sms')])
        if host_ids:        
            host_obj = self.pool.get('omg.configuration').browse(cr, uid, host_ids)[0]
            res.update({'user': host_obj['username'],'password':host_obj['password'],'app_id':'None'})
        return res

    def sms_send(self, cr, uid, ids, context):
        nbr = 0
                
        for data in self.browse(cr, uid, ids, context) :
            self.sms_send_by_thaibulksms(
                    data.user,
                    data.password, 
                    data.mobile_to,
                    data.text,
                    'SMS',
                    '',
                    'standard'
                    )
            nbr += 1
        return {}
partner_sms_send()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

