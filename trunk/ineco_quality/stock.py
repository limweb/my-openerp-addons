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

# 11-07-2012    POP-001    Add auto create when stock move done
# 21-07-2012    POP-002    Add QC Check in Stock Journal
# 31-07-2012    POP-003    Add Relation QC in LOT / Stock Move
#               POP-004    Check QC Approve before Issue/DO
# 01-08-2012    POP-005    Add QC Disable in Stock Picking

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

#POP-002
class stock_journal(osv.osv):
    
    _inherit = "stock.journal"
    _description = "Add QC Check in Stock Journal"
    _columns = {
        'ineco_qc_check': fields.boolean('Create QC Check'),
        'ineco_qc_approve': fields.boolean('Check QC Before Issue/Delivery'),
    }
    _defaults = {
        'ineco_qc_check': False,
        'ineco_qc_approve': False,
    }

stock_journal()

#POP-005
class stock_picking(osv.osv):
    _inherit = "stock.picking"
    _columns = {
        'qc_disable': fields.boolean('Disable QC'),
    }
    _defaults = {
        'qc_disable': True
    }
    
    def create(self, cr, user, vals, context=None):
        if not context:
            context = {}
        if ('qc_disable' in context):
            vals['qc_disable'] = False
        return super(stock_picking, self).create(cr, user, vals, context)
       
stock_picking()


class stock_move(osv.osv):
    
    def _get_qcpass(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        moves = self.browse(cr, uid, ids, context=context)
        for move in moves:
            qcpass = False
            if move.quality_ids:
                for qc in move.quality_ids:
                    if not qc.qc_pass:
                        qcpass = False
                        break
                    qcpass = qc.qc_pass
            else:
                qcpass = True
            res[move.id] = qcpass 
        return res

    def _get_qcnote(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        moves = self.browse(cr, uid, ids, context=context)
        for move in moves:            
            qcnote = ''
            if move.quality_ids:
                for qc in move.quality_ids:
                    qcnote = qc.note
            else:
                qcnote = 'No Check'
            res[move.id] = qcnote 
        return res
    
    _name = "stock.move"
    _inherit = "stock.move" 
    _description = "Add Quality Control/Assurance"
    _columns = {
        'ineco_quality_hold': fields.boolean('Hold'),
        'ineco_quality_pass': fields.boolean('Pass'),
        #POP-003
        'qc_pass': fields.function(_get_qcpass, string='QC Pass', method=True, type='boolean'),
        'qc_note': fields.function(_get_qcnote, string='QC Note', method=True, type='string'),
        'quality_ids': fields.one2many('ineco.quality.control', 'move_id', 'Quality Control')
    }
    _defaults = {
        'ineco_quality_hold': False,
        'ineco_quality_pass': False,
    }
    
    #POP-001
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if not isinstance(ids,list):
            ids = [ids]
        if 'state' in vals and vals['state'] == 'done':
            for sm in self.pool.get('stock.move').browse(cr, uid, ids):
                #POP-004
                if sm.picking_id and sm.picking_id.stock_journal_id and sm.picking_id.stock_journal_id.ineco_qc_approve:
                    if not sm.prodlot_id.qc_pass:
                        raise osv.except_osv(_('QC Not Pass !'), _('QC Not Pass!, Check information about ['+sm.product_id.name+']'))                
                    
                #POP-002
                use_quality_form = False
                if not use_quality_form:
                    #Form Incoming
                    use_quality_form = not sm.picking_id.stock_journal_id
                if not use_quality_form:
                    use_quality_form = sm.picking_id.stock_journal_id.ineco_qc_check
                
                #POP-005
                if use_quality_form and sm.product_id.ineco_quality_journal_id and not sm.picking_id.qc_disable :
                    quality_obj = self.pool.get('ineco.quality.control')
                    quality_ids = quality_obj.search(cr,uid,[('move_id','=',sm.id)])
                    partner_id = 1 #default
                    if sm.purchase_line_id and sm.purchase_line_id.partner_id:
                        partner_id = sm.purchase_line_id.partner_id.id
                    if not quality_ids:
                        new_data = {
                           'user_id': uid,
                           'product_id': sm.product_id.id,
                           'qc_force_pass': False,
                           'quality_journal_id': sm.product_id.ineco_quality_journal_id.id,
                           'uom_id': sm.product_uom.id,
                           'prodlot_id': sm.prodlot_id.id or False,
                           'date': time.strftime('%Y-%m-%d'),
                           'quantity': sm.product_qty,
                           'move_id': sm.id,
                           'picking_id': sm.picking_id.id or False,
                           'partner_id': partner_id,
                           'name': '/',
                        }
                        inv = sm.name.find('INV') #0 = False
                        if sm.name.find('INV') and not sm.scrapped:
                            quality_id = quality_obj.create(cr, uid, new_data)
        return super(stock_move, self).write(cr, uid, ids, vals, context=context)

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms stock move.
        @return: List of ids.
        """
        moves = self.browse(cr, uid, ids, context=context)
        self.write(cr, uid, ids, {'state': 'confirmed'})
        for move in moves:
            if move.product_id.ineco_quality and not move.ineco_quality_pass:
                 self.write(cr, uid, move.id, {'ineco_quality_hold': True, 'state':'waiting'})
        self.create_chained_picking(cr, uid, moves, context)
        return []
    
    def force_assign(self, cr, uid, ids, context=None):
        """ Changes the state to assigned.
        @return: True
        """
        moves = self.browse(cr, uid, ids, context=context)
        for move in moves:
            if not move.ineco_quality_hold or move.ineco_quality_pass:
                self.write(cr, uid, move.id, {'state': 'assigned'})
        return True
    
    def action_qcpass(self, cr, uid, ids, context=None):
        moves = self.browse(cr, uid, ids, context=context)
        for move in moves:
            self.write(cr, uid, move.id, {'ineco_quality_pass': True, 'state': 'done'})        
        return True
        
stock_move()

#POP-003
class stock_production_lot(osv.osv):
    
    def _get_qcpass(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        lots = self.browse(cr, uid, ids, context=context)
        for lot in lots:            
            qcpass = False
            if lot.quality_ids:
                for qc in lot.quality_ids:
                    if not qc.qc_pass:
                        qcpass = False
                        break
                    qcpass = qc.qc_pass
            else:
                qcpass = True            
            res[lot.id] = qcpass 
        return res
    
    _inherit = 'stock.production.lot'
    _description = "Quality Control of Lot"
    _columns = {
        'quality_ids': fields.one2many('ineco.quality.control', 'prodlot_id', 'Quality Control'),
        'qc_pass': fields.function(_get_qcpass, string='QC Pass', method=True, type='boolean'),
    }
stock_production_lot()