# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 INECO PARTNERSHIP LIMITED (<http://openerp.tititab.com>).
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

import wizard
from osv import osv
import pooler
from osv import fields
import time

from itertools import groupby
from operator import itemgetter
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def _launch_wizard(self, cr, uid, data, context=None):
    pool = pooler.get_pool(cr.dbname)
    if context is None:
        context = {}
    record_ids = data['ids']
    if record_ids:
        for record_id in record_ids:
            production = pool.get("mrp.production").browse(cr, uid, record_id)
            if production.state == 'draft':
                production.action_confirm()
                production.force_production()
            elif production.state == 'confirmed' or production.state == 'picking_except':
                production.force_production()
                
    return {}


class launch_form(wizard.interface):

    states= {'init' : {'actions': [],
                       'result':{'type':'action',
                                 'action': _launch_wizard,
                                 'state':'end'}
                       }
             }

launch_form('wizard_force_production')
