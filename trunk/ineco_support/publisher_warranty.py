# -*- coding: utf-8 -*-
##############################################################################
#
#    INECO, Information Engineering Consultance
#    www.tititab.com.
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

from osv import osv
from tools import cache

class publisher_warranty_contract(osv.osv):
    
    _inherit = 'publisher_warranty.contract'

    @cache(skiparg=3)
    def get_default_livechat_text(self, cr, uid):
        return '<a href="http://www.tititab.com" target="_blank"><img src="/web_livechat/static/images/busy.png"/>Support</a>'

publisher_warranty_contract()

