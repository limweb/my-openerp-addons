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

import math

from osv import fields,osv
import tools
import pooler
import uuid
from operator import itemgetter
from tools.translate import _

class res_partner(osv.osv):

    def _default_sync_id(self, cr, uid, context={}):
        #if 'category_id' in context and context['category_id']:
        #    return [context['category_id']]
        return str(uuid.uuid1())

    _name = "res.partner"    
    _inherit = "res.partner"

    _columns = {
        "ineco_sync_id":fields.char("Sync ID", size=36),
    }
    

    def create(self, cr, user, vals, context=None):
        if context is None:
            context = {}
        company_id = vals.get('company_id')
        partner_name = vals.get('name')
        sync_id = vals.get('ineco_sync_id')
        if not sync_id:
            sync_id = str(uuid.uuid1())     
            vals.update({'ineco_sync_id': sync_id}) 
            
        sql_company = """
            select company_id from res_partner
            where ineco_sync_id = '%s'
        """
        cr.execute(sql_company % sync_id)
        #company_dict = cr.dictfetchall()
        company_dict = map(itemgetter(0), cr.fetchall())        
        company_ids = self.pool.get('res.company').search(cr, user, [('id','not in',company_dict),('id','!=',company_id),('parent_id','!=',False)])
        new_id = super(res_partner,self).create(cr, user, vals, context)
        #super(res_partner, self).export_nav(cr, user, new_id, context)
        cr.commit()
        for row in company_ids:
            partner_exist_sql = """
              select id from res_partner where name = '%s' and company_id = %s
            """
            cr.execute(partner_exist_sql % (partner_name or "",row))
            exist_ids = cr.fetchall()
            if not exist_ids:
                vals.update({'company_id': row })
                row_id = super(res_partner,self).create(cr, user, vals, context)
            else:
                update_uuid_sql = "update res_partner set ineco_sync_id = '%s' where name = '%s' and company_id = %s"
                cr.execute(update_uuid_sql % (sync_id, partner_name, row))
            #super(res_partner, self).export_nav(cr, user, row_id, context)
        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        obj = self.read(cr, uid, ids)[0]
        sync_id = obj['ineco_sync_id']
        res_ids = ids
        if not sync_id:
            vals.update({'ineco_sync_id':str(uuid.uuid1())})
            res_ids = self.pool.get('res.partner').search(cr, uid, [('name','=',obj['name'])])
        else:
            res_ids = self.pool.get('res.partner').search(cr, uid, [('ineco_sync_id','=',sync_id)])
        return super(res_partner, self).write(cr, uid, res_ids, vals, context=context)

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

