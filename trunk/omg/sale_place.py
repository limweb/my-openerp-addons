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

import decimal_precision as dp

from osv import fields,osv
from tools.translate import _

class sale_place_department(osv.osv):
    _name = "sale.place.department"
    _description = "Sale place extend for Sale Order"

    _columns = {
        'name':fields.char('Department Name', size=64, select=True, required=True),
        'branch_ids': fields.one2many('sale.place.branch','department_id','Branch Lines')
    }    

sale_place_department()

class sale_place_area(osv.osv):
    _name = "sale.place.area"
    _description = "Sale place extend for Sale Order"

    _columns = {
        'name':fields.char('Area Name', size=64, select=True, required=True),
        'branch_ids': fields.one2many('sale.place.branch','area_id','Branch Lines')
    }    

sale_place_area()

class sale_place_group(osv.osv):
    _name = "sale.place.group"
    _description = "Sale place Extend for Sale Order"

    _columns = {
        'name':fields.char('Group Name', size=64, select=True, required=True),
        'branch_ids': fields.one2many('sale.place.branch','group_id','Branch Lines')
    }    

sale_place_group()

class sale_place_branch(osv.osv):
    _name = "sale.place.branch"
    _description = "Sale place Extend for Sale Order"

    _columns = {
        'name':fields.char('Branch Name', size=64, select=True, required=True),
        'department_id': fields.many2one('sale.place.department','Department',required=True, ondelete="restrict"),
        'area_id': fields.many2one('sale.place.area', 'Area', required=True, ondelete="restrict"),
        'group_id': fields.many2one('sale.place.group', 'Group', requirted=True, ondelete="restrict")
    }    

sale_place_branch()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
