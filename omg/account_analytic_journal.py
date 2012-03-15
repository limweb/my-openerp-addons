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

from osv import fields
from osv import osv

class account_analytic_journal(osv.osv):
    _name = 'account.analytic.journal'
    _inherit = 'account.analytic.journal'
    
    _columns = {
        'type': fields.selection([('sale','Sale'), ('purchase','Purchase'), ('cash','Cash'), ('general','General'), ('situation','Situation'),('budget','Budget')], 'Type', size=32, required=True, help="Gives the type of the analytic journal. When it needs for a document (eg: an invoice) to create analytic entries, OpenERP will look for a matching journal of the same type."),
        'account_budget_id': fields.many2one('account.account','Account ID', required=True, ondelete="restrict")
    }
    
account_analytic_journal()