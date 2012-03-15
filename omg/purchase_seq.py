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

class purchase_order(osv.osv):
    _name = "purchase.order"
    _inherit = "purchase.order"
    _defaults = {
        'name': lambda obj, cr, uid, context: '/'
        }

    def create(self, cr, user, vals, context=None):
        if ('name' not in vals) or (vals.get('name')=='/'):
            company_id = vals.get('company_id')
            seq_obj = self.pool.get('ir.sequence')
            seq_ids = seq_obj.search(cr, user, [('code','=','purchase.order'),('company_id','=',company_id)])
            sequence_id = 0
            if seq_ids:                
                sequence_id = seq_obj.browse(cr, user, seq_ids)[0].id
            else:
                raise osv.except_osv(_('Error !'), _('Can not find Purchase Sequence for Company.'))                
            vals['name'] = self.pool.get('ir.sequence').get_companyid(cr, user, sequence_id)
        return super(purchase_order,self).create(cr, user, vals, context)

purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

