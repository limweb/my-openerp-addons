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
import time
from osv import fields,osv
import pooler

class stock_move(osv.osv):
             
    _name = "stock.move"
    _inherit = "stock.move"
    _description = "Asset Link to Stock Move of OMG Holding (Thailand) Co.,Ltd."

    _columns = {
                'ineco_asset_register': fields.boolean('Ineco Asset Register'), 
    }

    _defaults = {
        'ineco_asset_register': False,
    }    

stock_move()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
