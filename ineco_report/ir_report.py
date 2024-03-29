# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 INECO PARNTERSHIP LIMITED (http://openerp.tititab.com) 
# All Right Reserved
#
# Author : Tititab Srisookco (thitithup@gmail.com)
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

from osv import osv, fields
import netsvc
from ineco_report import InecoParser
from report.report_sxw import rml_parse

def register_report(name, model, tmpl_path, parser=rml_parse):
    "Register the report into the services"
    name = 'report.%s' % name
    if netsvc.Service._services.get(name, False):
        service = netsvc.Service._services[name]
        if isinstance(service, InecoParser):
            #already instantiated properly, skip it
            return
        if hasattr(service, 'parser'):
            parser = service.parser
        del netsvc.Service._services[name]
    InecoParser(name, model, tmpl_path, parser=parser)


class ReportXML(osv.osv):

    def __init__(self, pool, cr):
        super(ReportXML, self).__init__(pool, cr)

    def register_all(self,cursor):
        value = super(ReportXML, self).register_all(cursor)
        cursor.execute("SELECT * FROM ir_act_report_xml WHERE report_type = 'ineco'")
        records = cursor.dictfetchall()
        for record in records:
            register_report(record['report_name'], record['model'], record['report_rml'])
        return value

    def unlink(self, cursor, user, ids, context=None):
        """Delete report and unregister it"""
        trans_obj = self.pool.get('ir.translation')
        trans_ids = trans_obj.search(
            cursor,
            user,
            [('type', '=', 'report'), ('res_id', 'in', ids)]
        )
        trans_obj.unlink(cursor, user, trans_ids)

        # Warning: we cannot unregister the services at the moment
        # because they are shared across databases. Calling a deleted
        # report will fail so it's ok.

        res = super(ReportXML, self).unlink(
                                            cursor,
                                            user,
                                            ids,
                                            context
                                        )
        return res

    def create(self, cursor, user, vals, context=None):
        "Create report and register it"
        res = super(ReportXML, self).create(cursor, user, vals, context)
        if vals.get('report_type','') == 'ineco':
            # I really look forward to virtual functions :S
            register_report(
                        vals['report_name'],
                        vals['model'],
                        vals.get('report_rml', False)
                        )
        return res

    def write(self, cr, uid, ids, vals, context=None):
        "Edit report and manage it registration"
        if isinstance(ids, (int, long)):
            ids = [ids,]
        for rep in self.browse(cr, uid, ids, context=context):
            if rep.report_type != 'ineco':
                continue
            if vals.get('report_name', False) and \
                vals['report_name'] != rep.report_name:
                report_name = vals['report_name']
            else:
                report_name = rep.report_name

            register_report(
                        report_name,
                        vals.get('model', rep.model),
                        vals.get('report_rml', rep.report_rml)
                        )
        res = super(ReportXML, self).write(cr, uid, ids, vals, context)
        return res

    _name = 'ir.actions.report.xml'
    _inherit = 'ir.actions.report.xml'
    _columns = {
        'jasper_url': fields.char('Jasper Server URL', size=254),
        'jasper_report_path': fields.char('Jaser Server Report Path', size=254),
        'jasper_username': fields.char('User Name', size=20),
        'jasper_password': fields.char('Password', size=20),
        'criteria_field': fields.char('Criteria Field', size=100),
        'parameter_name': fields.char('Jasper Parameter Name', size=100),
    }
    
    _defaults = {
        'report_type': 'ineco',
    }

ReportXML()
