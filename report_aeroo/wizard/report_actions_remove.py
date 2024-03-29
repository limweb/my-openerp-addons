##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import wizard
import pooler
import ir
from tools.translate import _

class report_actions_remove_wizard(wizard.interface):
    '''
    Remove print button
    '''
    form = '''<?xml version="1.0"?>
    <form string="Remove print button">
        <label string="Or you want to remove print button for this report?"/>
    </form>'''

    ex_form = '''<?xml version="1.0"?>
    <form string="Remove print button">
        <label string="No Report Action to delete for this report"/>
    </form>'''

    done_form = '''<?xml version="1.0"?>
    <form string="Remove print button">
        <label string="The print button is successfully removed"/>
    </form>'''

    def _do_action(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        report = pool.get(data['model']).browse(cr, uid, data['id'], context=context)
        res = ir.ir_get(cr, uid, 'action', 'client_print_multi', [report.model])
        id = res[0][0]
        res = ir.ir_del(cr, uid, id)
        return {}

    def _check(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        report = pool.get(data['model']).browse(cr, uid, data['id'], context=context)
        ids = pool.get('ir.values').search(cr, uid, [('value','=',report.type+','+str(data['id']))])
        if not ids:
	        return 'no_exist'
        else:
	        return 'remove'

    states = {
        'init': {
			'actions': [],
			'result': {'type':'choice','next_state':_check}
        },
        'remove': {
            'actions': [],
            'result': {'type': 'form', 'arch': form, 'fields': {}, 'state': (('end', _('_No')), ('process', _('_Yes')))},
        },
        'no_exist': {
            'actions': [],
            'result': {'type': 'form', 'arch': ex_form, 'fields': {}, 'state': (('end', _('_Close')),)},
        },
        'process': {
            'actions': [_do_action],
            'result': {'type': 'state', 'state': 'done'},
        },
        'done': {
            'actions': [],
            'result': {'type': 'form', 'arch': done_form, 'fields': {}, 'state': (('exit', _('_Close')),)},
        },
        'exit': {
            'actions': [],
            'result': {'type': 'state', 'state': 'end'},
        },
    }
report_actions_remove_wizard('aeroo.report_actions_remove')

