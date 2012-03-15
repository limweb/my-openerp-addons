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

import psycopg2

import wizard
import pooler
import netsvc
from tools.misc import UpdateableStr, UpdateableDict


_connection_arch = UpdateableStr()

def _test_connection(self,cr,uid,part,context={}):
    lines=pooler.get_pool(cr.dbname).get('olap.fact.database').browse(cr, uid, part['id'],context)
    host = lines.db_host
    port = lines.db_port
    db_name = lines.db_name
    user = lines.db_login
    password = lines.db_password
    type = lines.type
    return_str = "Connection Successful"
    try:	
        if type == 'postgres':
            print "postgres"
            tdb = psycopg2.connect('host=%s port=%s dbname=%s user=%s password=%s' % (host, port, db_name, user, password))
            #tdb = psycopg2.connect('host=%s port=%s dbname=%s user=%s password=%s' % (host, port, db_name, user, password), serialize=0, maxconn=64)

        elif type == 'mysql':
            import MySQLdb
            tdb = MySQLdb.connect(host = host,port = port, db = db, user = user, passwd = passwd)
                

        elif type == 'oracle':
            import cx_Oracle
            tdb = cx_Oracle.connect(user, password, host)
                
    except Exception, e:
            return_str = e.message

    _arch = ['''<?xml version="1.0"?>''', '''<form string="Connection Status">''']
    _arch.append('''<label string='%s' />''' % (return_str))
    _arch.append('''</form>''')
    _connection_arch.string = '\n'.join(_arch)

    return {}



class wizard_test_connection(wizard.interface):
    states = {
        'init': {
            'actions': [_test_connection],
            'result': {'type':'form', 'arch': _connection_arch, 'fields':{}, 'state':[('end','Ok')]}
        },
    }
wizard_test_connection('olap.fact.database.test_connection')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

