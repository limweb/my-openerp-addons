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
    'name': 'Extension for OMG Holding (Thailand) Co.,Ltd.',
    'version': '0.24',
    'category': 'Extension',
    'description': """This module will add some new requirement for OMG Holding (Thailand) Co,.Ltd.
    Please install depend module before install OMG Module
""",
    'author': 'INECO',
    'depends': ["base","stock","sale","purchase","ineco_multicompany","ineco_purchase_requisition",
                "purchase_requisition","procurement","ineco_communication","ineco_asset"],
    'website': 'http://openerp.tititab.com',
    'update_xml': [
        'omg_groups.xml',
        'wizard/wizard_location_set_view.xml',
        'wizard/wizard_force_delivery_confirm_view.xml',
        'purchase_requisition_view.xml',
        'analytic_data.xml',
        'stock_view.xml',
        'stock_chain_view.xml',                
        'omg_sale_order_copy_view.xml',        
        'sale_view.xml',
        'wizard/wizard_product_set_view.xml',
        'wizard/wizard_booking_checkprice_view.xml',
        'wizard/wizard_contact_merge_view.xml',
        'search_all_location.xml',        
        'search_all_wizard.xml',        
        'booking_wizard.xml',
        'procurement_view.xml',
        'account_analytic_view.xml',
        'default_report_data.xml',
        'product_view.xml',
        'wizard/purchase_requisition_partner_view.xml',
        'sale_contact_view.xml',
        'wizard/wizard_oa_report_view.xml',
        'omg_configuration_view.xml',
#        'wizard/wizard_report_incomming_view.xml',
#        'wizard/wizard_report_delivery_view.xml',
        'contact_data.xml',
        'wizard/wizard_report_delivery_summary_view.xml',
        'wizard/wizard_report_contact_list_view.xml',
        'account_analytic_journal_view.xml',
        'security/omg_security.xml',
        'secure_data.xml',
        'purchase_view.xml',
        #'security/ir.model.access.csv',
        'partner_view.xml',
        'wizard/wizard_report_summary_logistic_by_period_view.xml',
        'wizard/wizard_report_summary_booking_history_by_period_view.xml',
        'wizard/wizard_report_pivote_delivery_summary_by_period_view.xml',
        'wizard/wizard_ineco_dispatch_kitting_report_view.xml',
        'wizard/wizard_report_kitting_prepare_view.xml',
        'wizard/wizard_change_delivery_date_view.xml',
        'wizard/wizard_report_delivery_return_view.xml',
        'address_view.xml',
        'wizard/update_location_qty_view.xml',
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
