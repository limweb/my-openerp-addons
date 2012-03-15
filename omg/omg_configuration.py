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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class omg_configuration(osv.osv):

    _name = "omg.configuration"
    _description = "Configuration of OMG Holding (Thailand) Co.,Ltd."

    _columns = {
        'name':fields.char('Description', size=100, select=True, required=True),
        'host': fields.char('Host', size=50, required=True),
        'username': fields.char('User Name', size=50),
        'password': fields.char('Password', size=50),
        'type': fields.selection([('apache','Apache Host'),('jasper','Jasper Server'),('sms','SMS'),('booking','Apache Booking 2')], 'Type'),
        'url': fields.char('URL', size=250),
        'enable': fields.boolean('Enable'),
    }

    _defaults = {
        'name': '...',
        'enable': True
    }
    
omg_configuration()

class omg_purchase_email(osv.osv):
    _name = "omg.configuration.purchase.email"
    _description = "Email for Automation PR ->PO"
    
    _columns = {
        'name': fields.many2one('res.users', 'Purchase User',  ondelete='restrict', required=True),
        'active': fields.boolean('Active'),
    }
    
    _defaults = {
        'active': True,
    }
omg_purchase_email()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
