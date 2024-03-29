# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 INECO LTD, PARTNERSHIP (<http://www.ineco.co.th>).
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


# 26-03-2012    POP-001    Change OnCreate better way

import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _
from decimal import *
import decimal_precision as dp
import netsvc

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from operator import itemgetter
from itertools import groupby

class ineco_quality_journal(osv.osv):
    _name = "ineco.quality.journal"
    _description = "Ineco Quality Journal"
    _columns = {
        'name': fields.char('Ineco Quality Journal', size=32, required=True),
        'sequence_id': fields.many2one('ir.sequence', 'Sequence', required=True)
    }
    _defaults = {
    }

ineco_quality_journal()

class ineco_quality_category(osv.osv):
    _name = "ineco.quality.category"
    _description = "Ineco Quality Control/Assurance Category"
    _columns = {
        'name': fields.char('Description', size=255, required=True),
    }
    _sql_constraints = [
        ('quality_category_unizue', 'unique (name)', 'Description must be unique!')
    ]
    
ineco_quality_category()

class ineco_quality_item(osv.osv):
    _name = "ineco.quality.item"
    _description = "Ineco Quality Item"
    _columns = {
        'name': fields.char('Description', size=255, required=True),
        'category_id': fields.many2one('ineco.quality.category', 'Category', required=True),
    }
    _sql_constraints = [
        ('quality_item_unique', 'unique (name, category_id)', 'Description and Category must be unique!')
    ]
ineco_quality_item()

class ineco_quality_template(osv.osv):
    _name = "ineco.quality.template"
    _description = "Quality Control/Assurance Template"
    _columns = {
        'name': fields.char('Template Name', size=255, required=True),
        'line_ids' : fields.one2many('ineco.quality.template.line', 'template_id', 'Lines'),
    }
    _sql_constraints = [
        ('quality_template_name_unique', 'unique (name)', 'Template name must be unique!')
    ]    
ineco_quality_template()

class ineco_quality_template_line(osv.osv):
    _name = "ineco.quality.template.line"
    _description = "Quality Control/Assurance Template Line"
    _columns = {
        'name': fields.char('Method Description', size=255, required=True),
        'item_id': fields.many2one('ineco.quality.item', 'Item', required=True),       
        'template_id': fields.many2one('ineco.quality.template', 'Template'),
    }
ineco_quality_template_line()

class ineco_quality_control(osv.osv):
    
    def _get_pass(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for qc in self.browse(cr, uid, ids, context=context):
            qcpass = False
            if qc.line_ids:
                qcpass = True
                for line in qc.line_ids:
                    qcpass = qcpass and line.qc_pass
                if qc.qc_force_pass:
                    res[qc.id] = True
                else:
                    res[qc.id] = qcpass
            else:
                res[qc.id] = False 
        return res
        
    _name = "ineco.quality.control"
    _description = "Ineco Quality Control Form"
    _columns = {
        'name': fields.char('QC Number', size=64, required=True),
        'date': fields.date('Date', required=True),
        'user_id': fields.many2one('res.users', 'QC User', required=True),
        'picking_id': fields.many2one('stock.picking', 'Picking'),
        'move_id': fields.many2one('stock.move','Stock Move', reqruied=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'uom_id': fields.many2one('product.uom','UOM', required=True),
        'partner_id': fields.many2one('res.partner','Supplier', required=True),
        'prodlot_id': fields.many2one('stock.production.lot','Lot', required=True),
        'quantity': fields.float('Quantity', digits=(10,2), required=True),
        'line_ids': fields.one2many('ineco.quality.control.line','control_id','Lines'),
        'qc_pass': fields.function(_get_pass, string='Pass', method=True,  type='boolean', store=True),
        'quality_journal_id': fields.many2one('ineco.quality.journal','Quality Journal'),
        'qc_force_pass': fields.boolean('Force Pass'),
        'note': fields.text('Note'),
        'state':fields.selection(
            [('draft','Draft'),
             ('inprogress','In Progress'),
             ('done','Done'),
             ('cancel','Cancelled'),
            ], 'State', readonly=True, size=32),
    }
    _defaults = {
        'name': '/',
        'user_id': lambda self, cr, uid, context: uid,
        'date': lambda *a: time.strftime('%Y-%m-%d'), 
        'state':'draft',       
    }
    _order = "name desc"
    
    def act_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'inprogress'})
        return []

    def act_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'done'})
        return []

    def act_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'cancel'})
        return []

    def create(self, cr, user, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            if ('quality_journal_id' in vals) and (vals.get('quality_journal_id')):
                stock_journal = self.pool.get('ineco.quality.journal').browse(cr, user, [vals.get('quality_journal_id')])[0]
                if stock_journal:
                    seq_obj_name = stock_journal.sequence_id.code
                else:
                    seq_obj_name =  'ineco.quality.control'
            elif ('quality_journal_id' in context):
                stock_journal_ids = self.pool.get('ineco.quality.journal').search(cr, user, [('name','=',context['quality_journal_id'])])
                if stock_journal_ids:
                    stock_journal = self.pool.get('ineco.quality.journal').browse(cr, user, stock_journal_ids)[0]
                    if stock_journal:
                        vals['quality_journal_id'] = stock_journal.id
                        seq_obj_name = stock_journal.sequence_id.code
                    else:
                        seq_obj_name =  "ineco.quality.control"
            else:
                seq_obj_name =  'ineco.quality.control'
            #vals['name'] = self.pool.get('ir.sequence').get(cr, user, seq_obj_name)            
            #seq_obj_name =  'ineco.quality.control'
            vals['name'] = self.pool.get('ir.sequence').get(cr, user, seq_obj_name)
        new_id = super(ineco_quality_control, self).create(cr, user, vals, context)
        return new_id
    
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'name': self.pool.get('ir.sequence').get(cr, uid, 'ineco.quality.control'),
        })
        return super(ineco_quality_control, self).copy(cr, uid, id, default, context)    
    
ineco_quality_control()

class ineco_quality_control_line(osv.osv):

    def _get_pass(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        quality = self.browse(cr, uid, ids, context=context)
        for qc in quality:
            qcpass = True
            for line in qc.item_ids:
                qcpass = qcpass and line.qc_pass
            res[qc.id] = qcpass
        return res

    _name = "ineco.quality.control.line"
    _description = "Ineco Quality Control Line"
    _columns = {
        'name': fields.char('Description', size=254, required=True),
        'seq': fields.integer('Sequence', required=True),
        'note': fields.text('Notes'),
        'control_id': fields.many2one('ineco.quality.control', 'Quality Control', required=True),
        'item_ids': fields.one2many('ineco.quality.control.line.item','line_id','Items'),
        'qc_pass': fields.function(_get_pass, string='Pass', method=True,  type='boolean'),
    }
    _defaults = {
    }
    _order = "seq"

    def create(self, cr, user, vals, context=None):
        if vals.get('control_id'):
            data_ids = self.pool.get('ineco.quality.control.line').search(cr, user, [('control_id','=',vals.get('control_id'))])
            vals['seq'] = len(data_ids) + 1
        new_id = super(ineco_quality_control_line, self).create(cr, user, vals, context)
        return new_id
ineco_quality_control_line()

class ineco_quality_control_line_item(osv.osv):
    
    _name = "ineco.quality.control.line.item"
    _description = "Ineco Quality Control Line.item"
    _columns = {
        'name': fields.char('Description', size=254, required=True),
        'seq': fields.integer('Sequence', required=True),
        'item_id': fields.many2one('ineco.quality.item', 'QC Item'),
        'spec': fields.char('Specification', size=50),
        'sampling1': fields.char('Sampling 1', size=100),
        'sampling2': fields.char('Sampling 2', size=100),
        'result': fields.char('Result', size=254),
        'note': fields.text('Notes'),
        'line_id': fields.many2one('ineco.quality.control.line', 'Quality Control Line'),
        'qc_pass': fields.boolean('QC Pass'),
    }
    _defaults = {
        'qc_pass': False,
    }
    _order = "seq"
    
ineco_quality_control_line_item()

