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

from osv import fields,osv
from datetime import datetime
from tools.translate import _

class purchase_requisition(osv.osv):

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount': 0.0,
            }
            val = 0.0            
            for line in order.line_ids:
               val += (line.product_qty * line.product_cost)
            res[order.id]['amount'] = val 
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.requisition.line').browse(cr, uid, ids, context=context):
            result[line.requisition_id.id] = True
        return result.keys()

    def _get_po(self, cr, uid, ids, field_name, arg, context=None):
        po_sql = "select name from purchase_order where requisition_id = '%s'"
        res = {}
        for id in ids:
            po_list = ""
            cr.execute (po_sql % id)
            dict1 = cr.dictfetchall()
            for row in dict1:
                po_list = po_list+row['name']+','
            res[id] = po_list 
        return res

    _name = "purchase.requisition"
    _inherit = "purchase.requisition"
    _description="Extension of Purchase Requisition"
    _columns = {
        'budget': fields.many2one('account.analytic.account', 'Budget', required=True, ondelete="restrict"),
        'amount': fields.function(_amount_all, method=True, string='Amount',
            store={
                'purchase.requisition.line' : (_get_order, None, 10),
            }, multi="sums"),
        'user_support_id': fields.many2one('res.users', 'User Support', states={'draft': [('readonly', False)]}, ondelete='restrict', required=True),
        'date_pr_confirm': fields.datetime('PR Confirm Date'),
        'list_po': fields.function(_get_po, method=True, type='string', string='List PO'),        
    }
    
    _defaults = {
        #'date_start': time.strftime('%Y-%m-%d %H:%M:%S'),
        'date_start': False,
        'user_support_id': lambda obj, cr, uid, context: uid,
    }

    def tender_cancel(self, cr, uid, ids, context=None):
        tender_obj = self.browse(cr, uid, ids[0], context=context)        
        item_obj_id = self.pool.get('account.analytic.line').search(cr, uid, [('name', '=', tender_obj.name)], context=context)
        if item_obj_id:
            for item in item_obj_id:                
                item_id = self.pool.get('account.analytic.line').browse(cr,uid,item,context)
                self.pool.get('account.analytic.line').unlink(cr, uid, item_id.id)
                
        purchase_order_obj = self.pool.get('purchase.order')
        for purchase in self.browse(cr, uid, ids, context=context):
            for purchase_id in purchase.purchase_ids:
                if str(purchase_id.state) in('draft','wait'):
                    purchase_order_obj.action_cancel(cr,uid,[purchase_id.id])
        self.write(cr, uid, ids, {'state': 'cancel','date_pr_confirm':False})
        return True

    def tender_in_progress(self, cr, uid, ids, context=None):        
        obj = self.browse(cr, uid, ids[0], context=context)
        count_sql = "select count(*) as total from ir_attachment where res_model = 'purchase.requisition' and res_name = '%s' "
        cr.execute(count_sql % obj.name)
        dict1 = cr.dictfetchall()
        total_attachment = False
        for row in dict1:
            total_attachment = row['total']
        if not total_attachment:
            raise osv.except_osv(_('Warning !'), _('No File Attachment!.'))
        if obj.amount < obj.budget.balance:
            analytic_item_obj = self.pool.get('account.analytic.line');
            item = {
                'date': obj.date_start,
                'name': obj.name,
                'journal_id': self.pool.get('account.analytic.journal').search(cr, uid, [('code', '=', 'Budget')], context=context)[0],
                'amount' : -obj.amount,
                'account_id' : obj.budget.id ,
                'general_account_id' : self.pool.get('account.account').search(cr, uid, [('code', '=', '520300')], context=context)[0]
            }
            item_id = analytic_item_obj.create(cr, uid, item, context=context)
            
            purchase_email_obj = self.pool.get('omg.configuration.purchase.email')
            purchase_account_ids = self.pool.get('omg.configuration.purchase.email').search(cr, uid, [])
            purchase_account = self.pool.get('omg.configuration.purchase.email').browse(cr, uid, purchase_account_ids[0])
            
            email_obj = self.pool.get('email_template.mailbox')       
            email_account_id = self.pool.get('email_template.account').search(cr, uid, [('name', '=', 'ERP Mail Service')])[0]
            if email_account_id and purchase_account:
                email_id = email_obj.create(cr, uid, {
                    'email_from': 'ERP Email Agent',
                    'email_to': purchase_account.name.user_email,
                    'account_id': email_account_id ,
                    'subject': _('New PR: %s was approved by %s') % (obj.name, obj.user_id.user_email), #add pr no
                    'body_text': 'See in application. Thank you.' 
                })            
                email_obj.send_this_mail(cr, uid, [email_id])
            #date_pr_confirm
            self.write(cr, uid, ids, {'state':'in_progress','date_pr_confirm':time.strftime('%Y-%m-%d %H:%M:%S')} ,context=context)
            return True
        else:
            raise osv.except_osv(_('Warning !'), _('Your budget EXCEED!.'))

    def tender_reset(self, cr, uid, ids, context=None):
        tender_obj = self.browse(cr, uid, ids[0], context=context)        
        item_obj_id = self.pool.get('account.analytic.line').search(cr, uid, [('name', '=', tender_obj.name)], context=context)
        if item_obj_id:
            for item in item_obj_id:                
                item_id = self.pool.get('account.analytic.line').browse(cr,uid,item,context)
                self.pool.get('account.analytic.line').unlink(cr, uid, item_id.id)
        
        self.write(cr, uid, ids, {'state': 'draft','date_pr_confirm':False})
        return True

    def tender_done(self, cr, uid, ids, context=None):
        tender_obj = self.browse(cr, uid, ids[0], context=context)
        if not tender_obj.purchase_ids:
            raise osv.except_osv(_('Warning !'), _('Your not have RFQ or Purchase Order! Please contact Purchase Unit.')) 
        self.write(cr, uid, ids, {'state':'done', 'date_end':time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        return True

    def create(self, cr, user, vals, context=None):
        budget_ids = self.pool.get('account.analytic.account').search(cr, user, [("default_budget",'=',"True")])
        budget = False
        if budget_ids and ('budget' not in vals):
            budget = self.pool.get('account.analytic.account').browse(cr, user, budget_ids)[0]
            vals['budget'] = budget.id
        #else:
        #    raise osv.except_osv(_('Error !'), _('Cannot find Default Budget in this Company.')) 
                                   
        if ('name' not in vals) or (vals.get('name')=='/'):
            company_id = vals.get('company_id')
            seq_obj = self.pool.get('ir.sequence')
            seq_ids = seq_obj.search(cr, user, [('code','=','purchase.order.requisition'),('company_id','=',company_id)])
            sequence_id = 0
            if seq_ids:                
                sequence_id = seq_obj.browse(cr, user, seq_ids)[0].id
            else:
                raise osv.except_osv(_('Error !'), _('Can not find Purchase Requisition Sequence for Company.'))                
            vals['name'] = self.pool.get('ir.sequence').get_companyid(cr, user, sequence_id)
        return super(purchase_requisition,self).create(cr, user, vals, context)


purchase_requisition()

class purchase_requisition_line(osv.osv):

    _name = "purchase.requisition.line"
    _inherit = "purchase.requisition.line"
    _description="Extension of Purchase Requisition Line"

    _columns = {
        'product_cost': fields.float('Price', digits=(16,2)),
    }

    _defaults = {
        'product_cost': 0
    }

    def onchange_product_id(self, cr, uid, ids, product_id,product_uom_id, context=None):
        """ Changes UoM and name if product_id changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        value = {'product_uom_id': ''}
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            value = {'product_uom_id': prod.uom_id.id, 'product_qty':1.0, 'product_cost':prod.standard_price }
        return {'value': value}

purchase_requisition_line()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
