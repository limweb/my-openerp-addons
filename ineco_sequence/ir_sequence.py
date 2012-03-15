# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.openerp.com>
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

class ir_sequence(osv.osv):
    _name = "ir.sequence"
    _inherit = "ir.sequence"
    _columns = {
        'reset_nunber_month': fields.boolean('Reset Number Month'),
        'month_no': fields.integer('Month No.'),
    }
    _defaults = {
        'reset_nunber_month': False,
        'month_no' :time.strftime('%m'),
    }
    def get_id(self, cr, uid, sequence_id, test='id', context=None):
        assert test in ('code','id')
        company_id = self.pool.get('res.users').read(cr, uid, uid, ['company_id'], context=context)['company_id'][0] or None
        cr.execute('''SELECT id, number_next, month_no
                      FROM ir_sequence
                      WHERE %s=%%s
                       AND active=true
                       AND reset_nunber_month = true
                       AND (company_id = %%s or company_id is NULL)
                      ORDER BY company_id, id
                      FOR UPDATE NOWAIT''' % test,
                      (sequence_id, company_id))
        res = cr.dictfetchone()
        MonthNo = time.strftime('%m')
        if res:
            ResMonNO = str(res['month_no'])
            if ResMonNO != MonthNo:
                cr.execute('UPDATE ir_sequence SET number_next=1,month_no='+MonthNo+' WHERE id=%s AND active=true AND reset_nunber_month = true' , (res['id'],))        
        cr.execute('''SELECT id, number_next, prefix, suffix, padding
                      FROM ir_sequence
                      WHERE %s=%%s
                       AND active=true
                       AND (company_id = %%s or company_id is NULL)
                      ORDER BY company_id, id
                      FOR UPDATE NOWAIT''' % test,
                      (sequence_id, company_id))
        res = cr.dictfetchone()
        if res:
            cr.execute('UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s AND active=true', (res['id'],))
            if res['number_next']:
                return self._process(res['prefix']) + '%%0%sd' % res['padding'] % res['number_next'] + self._process(res['suffix'])
            else:
                return self._process(res['prefix']) + self._process(res['suffix'])
        return False

    def get(self, cr, uid, code):
        return self.get_id(cr, uid, code, test='code')
ir_sequence()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
