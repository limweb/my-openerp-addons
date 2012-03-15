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

from osv import fields, osv

class ir_sequence(osv.osv):
    _name = "ir.sequence"
    _inherit = "ir.sequence"

    def get_companyid(self, cr, uid, sequence_id, test='id', context=None):
        assert test in ('code','id')
        cr.execute('''SELECT id, number_next, prefix, suffix, padding
                      FROM ir_sequence
                      WHERE id = %s
                       AND active=true
                      FOR UPDATE NOWAIT''' % sequence_id)
        res = cr.dictfetchone()
        if res:
            cr.execute('UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s AND active=true', (res['id'],))
            if res['number_next']:
                return self._process(res['prefix']) + '%%0%sd' % res['padding'] % res['number_next'] + self._process(res['suffix'])
            else:
                return self._process(res['prefix']) + self._process(res['suffix'])
        return False


ir_sequence()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

