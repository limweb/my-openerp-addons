# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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


{
    'name': 'Extension for Google Maps',
    'version': '0.4',
    'category': 'Extension',
    'description': """
            Include Latitude and Longtitude
            This version only on Ubuntu and 

            sudo apt-get install apache2
            sudo apt-get install php5
            sudo apt-get install libapache2-mod-php5
            sudo /etc/init.d/apache2 restart
    
            and put file in php folder (all)

        """,
    'author': 'INECO LIMITED PARTNERSHIP',
    'depends': ["base"],
    'website': 'http://openerp.tititab.com',
    'update_xml': [
        "google_map_wizard.xml",
        "ineco_google_map_view.xml",
        "partner_address.xml",
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
