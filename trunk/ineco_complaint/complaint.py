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
import tools

from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import osv, fields
import netsvc
import pooler
from tools.translate import _
import decimal_precision as dp
from osv.orm import browse_record, browse_null

class ineco_complaint_category(osv.osv):
    _name = 'ineco.complaint.category'
    _description = "Category of Complaint"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'complaints': fields.many2many('ineco.complaint', 'groups_category_rel', 'gid', 'uid', 'Complaints'),
    }
    _sql_constraints = [
        ('complaint_category_uniq', 'unique (name)', 'Name of Category must be unique!')
    ]
ineco_complaint_category()

class ineco_complaint_response(osv.osv):
    _name = 'ineco.complaint.response'
    _description = "Response of Complaint"
    _columns = {
        'name': fields.char('Name',size=64,required=True),
        'complaints': fields.many2many('ineco.complaint', 'groups_response_rel', 'gid', 'uid', 'Complaints'),
    }
    _sql_constraints = [
        ('complaint_response_uniq', 'unique (name)', 'Name of Response must be unique!')
    ]
ineco_complaint_response()

class ineco_complaint(osv.osv):
    _name = "ineco.complaint"
    _description = "Customer complaint or Feed back record"
    _columns = {
        'name': fields.char("Complaint No", size=32, required=True),
        'date': fields.date("Complaint Date"),
        'type': fields.selection([('complaint','Complaint'), ('feedback','Feed Back')], 'Type', required=True),
        'problem': fields.text('Problem Statement', required=True),
        'category_id': fields.many2many('ineco.complaint.category', 'groups_category_rel', 'uid', 'gid', 'Categories'),
        'response_id': fields.many2many('ineco.complaint.response', 'groups_response_rel', 'uid', 'gid', 'Responses'),
        'solving': fields.selection([('immediately','Immediately'), ('inprogress','In Progress')], 'Solving'),
        'date_schedule': fields.date('Schedule Date'),
        'date_feedback': fields.date('Feedback Date'),
        'notes': fields.text('Note'),
        'comments': fields.text('Comments'),
        'user_id': fields.many2one('res.users', 'User')  
    }
    _defaults = {
        'user_id': lambda self, cr, uid, context: uid,
        'type': 'complaint',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'name': '/'
    }
    _order = "date"

    def create(self, cr, user, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            vals['name'] = self.pool.get('ir.sequence').get(cr, user, 'ineco.complaint')
        return super(ineco_complaint,self).create(cr, user, vals, context)

ineco_complaint()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

