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

class ineco_google_map(osv.osv):
    _name = 'ineco.google.map'
    _description ='Google Map Configuration'
    _columns = {
        "username": fields.char("User Name", size=64, required=True),
        "password": fields.char("Password", size=64, required=True),
        "dbname": fields.char("Database Name", size=64, required=True),
        "hostname": fields.char("Host Name", size=64, required=True),
    }
ineco_google_map()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

