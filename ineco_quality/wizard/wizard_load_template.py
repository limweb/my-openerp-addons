# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-TODAY INECO LIMITED PARTNERSHIP (<http://www.ineco.co.th>).
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

import decimal_precision as dp

from osv import fields, osv
from osv.orm import browse_record, browse_null
from tools.translate import _

class wizard_quality_load_template(osv.osv_memory):

    _name = "wizard.quality.load.template"
    _description = "Load Template Quality"
    _columns = {
        'name': fields.char('Name',size=100),
        'quality_template_id': fields.many2one('ineco.quality.template', 'Template', required=True),
        'state': fields.selection( ( ('choose','choose'), ('get','get'), ) ),
    }
    _defaults = {
        'name': '...',
        'state': 'choose',
    }

    def act_cancel(self, cr, uid, ids, context=None):
        #self.unlink(cr, uid, ids, context)
        return {'type':'ir.actions.act_window_close' }

    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    def add_template(self, cr, uid, ids, context):
        this = self.browse(cr, uid, ids)[0]
        if context is None:
            context = {}
        
        if this:
            quality_template_id = this.quality_template_id
            if quality_template_id:
                seq = 1
                for template in self.pool.get('ineco.quality.template').browse(cr, uid, [quality_template_id.id]):
                    line_data = {
                        'name': template.name,
                        'seq': seq,
                        'control_id': context['record_id']
                    }
                    seq = seq + 1
                    control_line_id = self.pool.get('ineco.quality.control.line').create(cr, uid, line_data)
                    line_seq = 1
                    for line in template.line_ids:
                        template_line_data = {
                            'name': line.name,
                            'seq': line_seq,
                            'item_id': line.item_id.id,
                            'line_id': control_line_id,
                        }
                        line_seq = line_seq + 1
                        detail_id = self.pool.get('ineco.quality.control.line.item').create(cr, uid, template_line_data)
            
        return {}
    
wizard_quality_load_template()




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
