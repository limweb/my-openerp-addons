# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 INECO PARTNERSHIP LIMITED (http://openerp.tititab.com)
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

{
    "name" : "Ineco Report Engine",
    "description" : """
                    """,
    "version" : "0.1",
    "depends" : ["base","ineco_base"],
    "author" : "INECO",
    "category": "Tools",
    "url": "http://openerp.tititab.com",
    "data": ["security.xml","ir_report_view.xml","ineco_report_view.xml"],
    "installable" : True,
    "active" : False,
}
