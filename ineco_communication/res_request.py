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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import osv, fields
import netsvc
import pooler
from tools.translate import _
import decimal_precision as dp
from osv.orm import browse_record, browse_null


class res_request(osv.osv):
    _name = 'res.request'
    _inherit = 'res.request'
    _description = 'Add send mail from request'
    
    def request_send(self, cr, uid, ids, *args):
        super(res_request,self).request_send(cr, uid, ids, *args)
        for id in ids:
            pr_obj = self.pool.get('res.request').browse(cr, uid, [id])[0]
            if pr_obj:
                email_obj = self.pool.get('email_template.mailbox')   
                email_account_id = self.pool.get('email_template.account').search(cr, uid, [('name', '=', 'ERP Mail Service')])[0]
                if email_account_id:
                    #print po.requisition_id.user_id.user_email
                    #print email_cc
                    email_id = email_obj.create(cr, uid, {
                        'email_from': 'ERP Email Agent',
                        'email_to': pr_obj.act_to.user_email,
                        'email_cc': pr_obj.act_from.user_email,
                        'account_id': email_account_id ,
                        'subject': pr_obj.name ,
                        'body_text': pr_obj.body, 
                    })            
                    email_obj.send_this_mail(cr, uid, [email_id])
res_request()