# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import urllib
from urllib import urlopen, urlencode, unquote

import urllib2

import simplejson
import wizard
import pooler
import re

trans_form = '''<?xml version="1.0"?>
    <form string="Translation" colspan="4">
         <newline/>
         <label string="This wizard will translate terms in source using google for given language" align="0.0" colspan="3"/>
         <newline/>
     </form> '''
trans_fields = { }

trans_sum = '''<?xml version="1.0"?>
        <form string="Translation" colspan="4">
             <newline/>
             <label string="Successfullly Translate" />
             <newline/>
        </form> '''
trans_sum_fields = { }

def setUserAgent(userAgent):
    urllib.FancyURLopener.version = userAgent
    pass

def _translate(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    tran_obj = pool.get('ir.translation')
    key_obj = pool.get('tititab.translate.key')
    key_ids = key_obj.search(cr, uid, [("default","=",1)])
    google_key = key_obj.read(cr, uid, key_ids, ['name'], context)
    print google_key
    
    in_lang = 'en'
    ids = data['ids']
    translation_data = tran_obj.browse(cr, uid, ids, context)

    for trans in translation_data:

        out_lang = trans['lang'][:2].lower().encode('utf-8')
        src = trans['src'].encode('utf-8')
        setUserAgent("Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008070400 SUSE/3.0.1-0.1 Firefox/3.0.1")

        post_params = urllib.urlencode({"key":google_key[0]['name'], "q":src, "source":in_lang, "target":out_lang})

        url = 'https://www.googleapis.com/language/translate/v2?'+post_params
        print url
        request = urllib2.Request(url, None, {'Referer': 'http://openerp.tititab.com'})
        response = urllib2.urlopen(request)

        results = simplejson.load(response)
        
        value = src
        if results:
            value = results['data']['translations'][0]['translatedText']
        tran_obj.write(cr, uid, trans.id, {'value':value})
    return {}

class google_translate_wizard(wizard.interface):
    states = {
        'init': {
             'actions': [],
                'result': {'type': 'form', 'arch':trans_form, 'fields':trans_fields, 'state':[('end','Cancel','gtk-cancel'),('translate','Translate','gtk-ok')]}
                },
        'translate': {
                'actions': [_translate],
                'result': {'type': 'form', 'arch':trans_sum, 'fields':trans_sum_fields, 'state':[('end','OK','gtk-ok')]}
                },
            }

google_translate_wizard('tititab.translate.wizard')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
