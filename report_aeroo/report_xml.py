##############################################################################
#
# Copyright (c) 2009-2011 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
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

from osv import osv,fields
import netsvc
from report_aeroo import Aeroo_report
from report.report_sxw import rml_parse
import base64, binascii
import tools
import encodings
from tools.translate import _

import imp, sys, os
import zipimport
from tools.config import config

class report_stylesheets(osv.osv):
    '''
    Open ERP Model
    '''
    _name = 'report.stylesheets'
    _description = 'Report Stylesheets'
    
    _columns = {
        'name':fields.char('Name', size=64, required=True),
        'report_styles' : fields.binary('Template Stylesheet', help='OpenOffice.org stylesheet (.odt)'),
        
    }

report_stylesheets()

class res_company(osv.osv):
    _name = 'res.company'
    _inherit = 'res.company'

    _columns = {
        #'report_styles' : fields.binary('Report Styles', help='OpenOffice stylesheet (.odt)'),
        'stylesheet_id':fields.many2one('report.stylesheets', 'Aeroo Global Stylesheet'),
    }

res_company()

class report_mimetypes(osv.osv):
    '''
    Aeroo Report Mime-Type
    '''
    _name = 'report.mimetypes'
    _description = 'Report Mime-Types'
    
    _columns = {
        'name':fields.char('Name', size=64, required=True, readonly=True),
        'code':fields.char('Code', size=16, required=True, readonly=True),
        'compatible_types':fields.char('Compatible Mime-Types', size=128, readonly=True),
        'filter_name':fields.char('Filter Name', size=128, readonly=True),
        
    }

report_mimetypes()

class report_xml(osv.osv):
    _name = 'ir.actions.report.xml'
    _inherit = 'ir.actions.report.xml'

    def load_from_file(self, path, dbname, key):
        class_inst = None
        expected_class = 'Parser'

        try:
            mod_path = config['addons_path']+os.path.sep+path.split(os.path.sep)[0]
            if os.path.lexists(mod_path):
                filepath=config['addons_path']+os.path.sep+path
                filepath = os.path.normpath(filepath)
                sys.path.append(os.path.dirname(filepath))
                mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
                mod_name = '%s_%s_%s' % (dbname,mod_name,key)

                if file_ext.lower() == '.py':
                    py_mod = imp.load_source(mod_name, filepath)

                elif file_ext.lower() == '.pyc':
                    py_mod = imp.load_compiled(mod_name, filepath)

                if expected_class in dir(py_mod):
                    class_inst = py_mod.Parser
                return class_inst
            elif os.path.lexists(mod_path+'.zip'):
                zimp = zipimport.zipimporter(mod_path+'.zip')
                return zimp.load_module(path.split(os.path.sep)[0]).parser.Parser
        except Exception, e:
            return None

    def load_from_source(self, source):
        expected_class = 'Parser'
        context = {'Parser':None}
        try:
            exec source in context
            return context['Parser']
        except Exception, e:
            return None

    def delete_report_service(self, name):
        name = 'report.%s' % name
        if netsvc.Service.exists( name ):  # change for OpenERP 6.0 - Service class usage
            netsvc.Service.remove( name ) # change for OpenERP 6.0 - Service class usage

    def register_report(self, cr, name, model, tmpl_path, parser):
        name = 'report.%s' % name
        if netsvc.Service.exists( name ):  # change for OpenERP 6.0 - Service class usage
            netsvc.Service.remove( name ) # change for OpenERP 6.0 - Service class usage
        Aeroo_report(cr, name, model, tmpl_path, parser=parser)

    def register_all(self, cr):
        ########### Run OpenOffice service ###########
        try:
            from report_aeroo_ooo.report import OpenOffice_service
        except Exception, e:
            OpenOffice_service = False

        if OpenOffice_service:
            cr.execute("SELECT id, state FROM ir_module_module WHERE name='report_aeroo_ooo'")
            helper_module = cr.dictfetchone()
            helper_installed = helper_module['state']=='installed'

        if OpenOffice_service and helper_installed:
            cr.execute("SELECT host, port FROM oo_config")
            host, port = cr.fetchone()
            try:
                OpenOffice_service(cr, host, port)
                netsvc.Logger().notifyChannel('report_aeroo', netsvc.LOG_INFO, "OpenOffice.org connection successfully established")
            except Exception, e:
                netsvc.Logger().notifyChannel('report_aeroo', netsvc.LOG_WARNING, e)
        ##############################################

        cr.execute("SELECT * FROM ir_act_report_xml WHERE report_type = 'aeroo' ORDER BY id") # change for OpenERP 6.0
        records = cr.dictfetchall()
        for record in records:
            parser=rml_parse
            if record['parser_state']=='loc' and record['parser_loc']:
                parser=self.load_from_file(record['parser_loc'], cr.dbname, record['id']) or parser
            elif record['parser_state']=='def' and record['parser_def']:
                parser=self.load_from_source("from report import report_sxw\n"+record['parser_def']) or parser
            self.register_report(cr, record['report_name'], record['model'], record['report_rml'], parser)


    def _report_content(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for report in self.browse(cursor, user, ids, context=context):
            data = report[name + '_data']# and base64.decodestring(report[name + '_data'])
            if not data and report[name[:-8]]:
                try:
                    fp = tools.file_open(report[name[:-8]], mode='rb')
                    data = base64.encodestring(fp.read())
                except:
                    data = ''
            res[report.id] = data
        return res

    def _get_encodings(self, cursor, user, context={}):
        l = list(set(encodings._aliases.values()))
        l.sort()
        return zip(l, l)

    def _report_content_inv(self, cursor, user, id, name, value, arg, context=None):
        if value:
            self.write(cursor, user, id, {name+'_data': value}, context=context)

    def change_input_format(self, cr, uid, ids, in_format):
        out_format = self.pool.get('report.mimetypes').search(cr, uid, [('code','=',in_format)])
        return {
            'value':{'out_format': out_format and out_format[0] or False}
        }

    def _get_in_mimetypes(self, cr, uid, context={}):
        obj = self.pool.get('report.mimetypes')
        ids = obj.search(cr, uid, [('filter_name','=',False)], context=context)
        res = obj.read(cr, uid, ids, ['code', 'name'], context)
        return [(r['code'], r['name']) for r in res] + [('','')]

    _columns = {
        'charset':fields.selection(_get_encodings, string='Charset', required=True),
        'content_fname': fields.char('Override Extension',size=64, help='Here you can override output file extension'),
        'styles_mode': fields.selection([
            ('default','Not used'),
            ('global', 'Global'),
            ('specified', 'Specified'),
            ], string='Stylesheet'),
        #'report_styles' : fields.binary('Template Styles', help='OpenOffice stylesheet (.odt)'),
        'stylesheet_id':fields.many2one('report.stylesheets', 'Template Stylesheet'),
        'preload_mode':fields.selection([
            ('static',_('Static')),
            ('preload',_('Preload')),
        ],'Preload Mode'),
        'tml_source':fields.selection([
            ('database','Database'),
            ('file','File'),
            ('parser','Parser'),
        ],'Template source', select=True),
        'parser_def': fields.text('Parser Definition'),
        'parser_loc':fields.char('Parser location', size=128, help="Path to the parser location. Beginning of the path must be start with the module name!\nLike this: {module name}/{path to the parser.py file}"),
        'parser_state':fields.selection([
            ('default',_('Default')),
            ('def',_('Definition')),
            ('loc',_('Location')),
        ],'State of Parser', select=True),
        'in_format': fields.selection(_get_in_mimetypes, 'Template Mime-type'),
        'out_format':fields.many2one('report.mimetypes', 'Output Mime-type'),
        'report_sxw_content': fields.function(_report_content,
            fnct_inv=_report_content_inv, method=True,
            type='binary', string='SXW content',),
    }

    def unlink(self, cr, uid, ids, context=None):
        #TODO: process before delete resource
        trans_obj = self.pool.get('ir.translation')
        trans_ids = trans_obj.search(cr, uid, [('type','=','report'),('res_id','in',ids)])
        trans_obj.unlink(cr, uid, trans_ids)
        ####################################
        reports = self.read(cr, uid, ids, ['report_name','model'])
        for r in reports:
            ir_value_ids = self.pool.get('ir.values').search(cr, uid, [('name','=',r['report_name']), 
                                                                            ('value','=','ir.actions.report.xml,%s' % r['id']),
                                                                            ('model','=',r['model'])
                                                                            ])
            if ir_value_ids:
                self.pool.get('ir.values').unlink(cr, uid, ir_value_ids)
        self.pool.get('ir.model.data')._unlink(cr, uid, 'ir.actions.report.xml', ids)
        ####################################
        res = super(report_xml, self).unlink(cr, uid, ids, context)
        return res

    def create(self, cr, user, vals, context={}):
        #if context and not self.pool.get('ir.model').search(cr, user, [('model','=',vals['model'])]):
        #    raise osv.except_osv(_('Object model is not correct !'),_('Please check "Object" field !') )
        if 'report_type' in vals and vals['report_type'] == 'aeroo':
            parser=rml_parse
            if vals['parser_state']=='loc' and vals['parser_loc']:
                parser=self.load_from_file(vals['parser_loc'], cr.dbname, vals['name'].lower().replace(' ','_')) or parser
            elif vals['parser_state']=='def' and vals['parser_def']:
                parser=self.load_from_source("from report import report_sxw\n"+vals['parser_def']) or parser

            res_id = super(report_xml, self).create(cr, user, vals, context)
            try:
                self.register_report(cr, vals['report_name'], vals['model'], vals.get('report_rml', False), parser)
            except Exception, e:
                raise osv.except_osv(_('Report registration error !'), _('Report was not registered in system !'))
            return res_id

        res_id = super(report_xml, self).create(cr, user, vals, context)
        return res_id

    def write(self, cr, user, ids, vals, context=None):
        if 'report_sxw_content_data' in vals:
            if vals['report_sxw_content_data']:
                try:
                    base64.decodestring(vals['report_sxw_content_data'])
                except binascii.Error:
                    vals['report_sxw_content_data'] = False
        if type(ids)==list:
            ids = ids[0]
        record = self.read(cr, user, ids)
        #if context and 'model' in vals and not self.pool.get('ir.model').search(cr, user, [('model','=',vals['model'])]):
        #    raise osv.except_osv(_('Object model is not correct !'),_('Please check "Object" field !') )
        if vals.get('report_type', record['report_type']) == 'aeroo':
            parser=rml_parse
            if vals.get('parser_state', False)=='loc':
                parser = self.load_from_file(vals.get('parser_loc', False) or record['parser_loc'], cr.dbname, record['id']) or parser
            elif vals.get('parser_state', False)=='def':
                parser = self.load_from_source("from report import report_sxw\n"+(vals.get('parser_loc', False) or record['parser_def'] or '')) or parser
            elif vals.get('parser_state', False)=='default':
                parser = rml_parse
            elif record['parser_state']=='loc':
                parser = self.load_from_file(record['parser_loc'], cr.dbname, record['id']) or parser
            elif record['parser_state']=='def':
                parser = self.load_from_source("from report import report_sxw\n"+record['parser_def']) or parser
            elif record['parser_state']=='default':
                parser = rml_parse

            if vals.get('parser_loc', False):
                parser=self.load_from_file(vals['parser_loc'], cr.dbname, record['id']) or parser
            elif vals.get('parser_def', False):
                parser=self.load_from_source("from report import report_sxw\n"+vals['parser_def']) or parser
            if vals.get('report_name', False) and vals['report_name']!=record['report_name']:
                self.delete_report_service(record['report_name'])
                report_name = vals['report_name']
            else:
                self.delete_report_service(record['report_name'])
                report_name = record['report_name']

            res = super(report_xml, self).write(cr, user, ids, vals, context)
            try:
                self.register_report(cr, report_name, vals.get('model', record['model']), vals.get('report_rml', record['report_rml']), parser)
            except Exception, e:
                raise osv.except_osv(_('Report registration error !'), _('Report was not registered in system !'))
            return res

        res = super(report_xml, self).write(cr, user, ids, vals, context)
        return res

    def _get_default_outformat(self, cr, uid, context):
        obj = self.pool.get('report.mimetypes')
        res = obj.search(cr, uid, [('code','=','oo-odt')])
        return res and res[0] or False

    _defaults = {
        #'report_type' : lambda*a: 'oo-odt',
        'tml_source': lambda*a: 'database',
        'in_format' : lambda*a: 'oo-odt',
        'out_format' : _get_default_outformat,
        'charset': lambda*a: 'ascii',
        'styles_mode' : lambda*a: 'default',
        'preload_mode': lambda*a: 'static',
        'parser_state': lambda*a: 'default',
        'parser_def':lambda*a: """class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({})"""
    }

    #def _object_check(self, cr, uid, ids):
    #    for r in self.browse(cr, uid, ids, {}):
    #        if not self.pool.get('ir.model').search(cr, uid, [('model','=',r.model)]):
    #            return False
    #    return True

    #_constraints = [
    #        (_object_check, _('Object model is not correct')+' !\n'+_('Please check "Object" field')+' !', ['model'])
    #    ]

report_xml()

class ir_translation(osv.osv):
    _name = 'ir.translation'
    _inherit = 'ir.translation'

    def __init__(self, pool, cr):
        super(ir_translation, self).__init__(pool, cr)
        if ('report', 'Report') not in self._columns['type'].selection:
            self._columns['type'].selection.append(
                        ('report', 'Report'),
                    )

ir_translation()

