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

import math

from osv import fields,osv
import tools
import pooler
from tools.translate import _

class res_partner_address(osv.osv):
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'
    _description ='Partner Addresses'
    _columns = {
        "latitude": fields.float("Latitude", digits=(20,16)),
        "longtitude": fields.float("Longtidue", digits=(20,16)),
    }
res_partner_address()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

