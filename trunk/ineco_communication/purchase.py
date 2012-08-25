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

# Date             ID         Message
# 23-08-2012       DAY-001    Email Text 
# 25-08-2012       DAY-002    Create RFQ Not Send Email


import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import osv, fields
import netsvc
import pooler
from tools.translate import _
import decimal_precision as dp
from osv.orm import browse_record, browse_null

#
# Model definition
#
class purchase_order(osv.osv):

    def _send_mail(self, cr, uid, ids, status):
        email_cc_name = self.pool.get('res.users').browse(cr, uid, uid).name
        email_cc = self.pool.get('res.users').browse(cr, uid, uid).user_email
        for po in self.browse(cr, uid, ids):
            if po.requisition_id:        
                email_obj = self.pool.get('email_template.mailbox')       
                email_account_id = self.pool.get('email_template.account').search(cr, uid, [('name', '=', 'ERP Mail Service')])[0]
                if email_account_id:
                    #print po.requisition_id.user_id.user_email
                    #print email_cc
                    email_id = email_obj.create(cr, uid, {
                        'email_from': 'ERP Email Agent',
                        'email_to': po.requisition_id.user_id.user_email,
                        'email_cc': po.requisition_id.user_support_id.user_email or '',
                        'account_id': email_account_id ,
                        'subject': _('Purchase order : %s has been %s (include PR: %s) by %s') % (po.name,status,po.requisition_id.name,email_cc_name) ,
                        'body_text': 'Please check your order in ERP Software. Thank you.' 
                    })			
                    email_obj.send_this_mail(cr, uid, [email_id])
        return True

    _name = "purchase.order"
    _inherit = "purchase.order"

    def create(self, cr, user, vals, context=None):        
        po_id = super(purchase_order,self).create(cr, user, vals, context)
        #DAY-002
        #if ('requisition_id' in vals):
        #    self._send_mail(cr, user, [po_id], 'issued') #DAY-001
        return po_id

    def wkf_approve_order(self, cr, uid, ids, context=None):
        super(purchase_order,self).wkf_approve_order(cr, uid, ids, context)
        return True

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        super(purchase_order,self).wkf_confirm_order(cr, uid, ids, context)
        self._send_mail(cr, uid, ids, 'submitted') #DAY-001
        return True

    def action_cancel_draft(self, cr, uid, ids, *args):
        super(purchase_order,self).action_cancel_draft(cr, uid, ids, *args)
        self._send_mail(cr, uid, ids, 'drafted')
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        super(purchase_order,self).action_cancel(cr, uid, ids, context)
        self._send_mail(cr, uid, ids, 'canceled')
        return True

purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
