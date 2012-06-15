# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

# 18-02-2012    POP-001    Create ineco.query.stock.report (Dispatch VS Kitting) 
# 27-02-2012    POP-002    Add Max Category in stock.location.booking
# 25-03-2012    POP-003    Add Copy to Stock.picking
# 11-04-2012    POP-004    Change way to send sms
# 11-04-2012    POP-005    Change uom default when not in same category
# 17-04-2012    POP-006    Add ineco.stock.location.product.mapping
# 02-05-2012    DAY-001    Add OMG Field
# 11-06-2012    POP-007    Check Stock Before Intermal Move
# 13-06-2012    POP-008     Lock Stock Move When state 'Done'

import socket
import sys

import time
import netsvc
import asset

import sale
import sale_period

import decimal_precision as dp

from osv import fields,osv
from tools.translate import _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

import re

import tools 

def toHex(s):
    lst = []
    #s = s.replace(' ','')
    for ch in s:
        hv = hex(ord(ch)).replace('0x', '0')
        if len(hv) < 4:
            hv = '0'+hv
        else:
            hv = hv
        hv = '%'+hv[:2]+'%'+hv[2:]
        lst.append(hv.upper())
    
    return reduce(lambda x,y:x+y, lst)

def send_sms(host, post, message):
    host = '192.168.1.108'    # The remote host
    port = 81              # The same port as used by the server
    message = "OK Na ja"
    s = None
    for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        try:
            s = socket.socket(af, socktype, proto)
        except socket.error, msg:
            s = None
            continue
        try:
            s.connect(sa)
        except socket.error, msg:
            s.close()
            s = None
            continue
        break
    if s is None:
        print 'could not open socket'
        sys.exit(1)
    
    data  = "TRANSID=BULK&CMD=SENDMSG&FROM=9009000&TO=6691306226&REPORT=Y&CHARGE=Y&CODE=TEXT&CTYPE=UNICODE&CONTENT="+message
    length = len(data)
    package = "POST / HTTP/1.1\r\nContent-type:application/x-www-form-urlencoded\r\nContent-length: %d\r\n\r\n%s" % (length,data.encode('utf-8'))
    s.send(package)
    data = s.recv(1024)
    s.close()
    print 'Received', repr(data)  #wait parsing xml and record in database
    return True  

class stock_move(osv.osv):
       
    def _get_date_arrival_planned(self, cr, uid, ids, prop, unknow_none, context=None):
        """ Finds production planned date.
        @param prop: Name of field.
        @param unknow_none:
        @return: Dictionary of values.
        """
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.picking_id and line.picking_id.date_arrival:
                result[line.id] = line.picking_id.date_arrival
        return result

    def _get_date_period_start(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.period_id:
                res[line.id] = line.period_id.date_start
        return res
       
    _name = "stock.move"
    _inherit = "stock.move"
    _description = "Asset Link to Stock Move of OMG Holding (Thailand) Co.,Ltd."

    _columns = {
        'customer_product_id': fields.many2one('product.product', 'Customer Product', ondelete='restrict' ),
        'period_id': fields.many2one('omg.sale.period','Period', ondelete='restrict'),
        'date_arrival': fields.datetime("Arrival Date"),
        'date_completed': fields.datetime("Complete Date"),
        'date_finished': fields.datetime("Finish Date"),
        'state': fields.selection([('draft', 'Draft'), ('waiting', 'Waiting'), ('confirmed', 'Not Available'), ('assigned', 'Available'), ('done', 'Done'), ('cancel', 'Cancelled'),('wait2','Wait Arrival'),('arrival','Arrival'),('complete','Complete'),('complete2','Force Complete')], 'State', readonly=True, select=True,
              help='When the stock move is created it is in the \'Draft\' state.\n After that, it is set to \'Not Available\' state if the scheduler did not find the products.\n When products are reserved it is set to \'Available\'.\n When the picking is done the state is \'Done\'.\
              \nThe state is \'Waiting\' if the move is waiting for another one.'),
        'date_appointment': fields.datetime('Appointment Date'),
        'receive_qty': fields.float('Receive Qty', digits_compute=dp.get_precision('Account')),
        'date_arrival_planned': fields.datetime(string='Arrival Planned'),
        'date_period_start': fields.function(_get_date_period_start, method=True, type='datetime', string='Period Date'),
        'date_audit': fields.datetime('Audit Date'),        
        'date_forced': fields.datetime('Force Date'),
        'user_forced': fields.many2one('res.users', 'Force User',),
    }

    _defaults = {
        'receive_qty': 0,
    }    

    def action_done(self, cr, uid, ids, context=None):
        move_ids = self.pool.get('stock.move').browse(cr, uid, ids)
        for move in move_ids:
            #POP-007
            if move.picking_id.type == 'internal':
                if move.location_id.usage == 'internal':
                    stock_ids = self.pool.get("ineco.stock.report").search(cr, uid, [('location_dest_id','=',move.location_id.id),('lot_id','=',move.prodlot_id.id),('tracking_id','=',move.tracking_id.id),('qty','>',0)])
                    max_qty = 0
                    for stock in self.pool.get("ineco.stock.report").browse(cr, uid, stock_ids):
                        max_qty += stock.qty
                    if round(move.product_qty / move.product_uom.factor) > max_qty:
                        raise osv.except_osv(_('Error'), _('Stock Unavailable -> '+move.product_id.name+'.' ))                        
            #POP-005
            if move.product_uom.category_id.id <> move.product_id.uom_id.category_id.id:
                raise osv.except_osv(_('Error'), _('UOM Category Error, Please check-> '+move.product_id.name+' in product master.' ))
                new_uom = move.product_id.uom_id.id
            else:
                new_uom = move.product_uom.id
            if move.picking_id.date_done:
                move.write({'date_finished': move.picking_id.date_done, 'product_uom':new_uom})
            else:
                move.write({'date_finished': time.strftime('%Y-%m-%d %H:%M:%S'), 'product_uom':new_uom})
        super(stock_move, self).action_done(cr, uid, ids, context)
        return True

    def action_arrival(self, cr, uid, ids, context=None):
        ##please check none value only
        move_obj = self.pool.get('stock.move').browse(cr, uid, ids)
        new_qty = 0
        receive_qty = 0
        product_qty = 0
        if move_obj:
            receive_qty = move_obj[0].receive_qty
            product_qty = move_obj[0].product_qty
        if receive_qty == 0:
            new_qty = product_qty
        else:
            new_qty = receive_qty
        if not move_obj[0].date_appointment:
            arrival_date = date.today() + timedelta(days=7)
            #self.write(cr, uid, ids, {'date_arrival': time.strftime('%Y-%m-%d %H:%M:%S'),'date_appointment':arrival_date.strftime('%Y-%m-%d %H:%M:%S') , 'state':'arrival' ,'receive_qty':new_qty})
            self.write(cr, uid, ids, {'date_arrival': time.strftime('%Y-%m-%d %H:%M:%S'),'date_appointment':arrival_date.strftime('%Y-%m-%d %H:%M:%S') , 'state':'arrival' ,'receive_qty':new_qty})
        else:
            #self.write(cr, uid, ids, {'date_arrival': time.strftime('%Y-%m-%d %H:%M:%S'), 'state':'arrival' ,'receive_qty':new_qty})
            self.write(cr, uid, ids, {'date_arrival': time.strftime('%Y-%m-%d %H:%M:%S'), 'state':'arrival' ,'receive_qty':new_qty})
        oa_name = move_obj[0].picking_id.address_id.name
        oa_mobile_no = move_obj[0].picking_id.address_id.mobile
        if oa_mobile_no:        
            oa_mobile_no = re.sub(r'\D',"",oa_mobile_no)
        
        #oa_name = oa_name.replace(' ','')
        
        if oa_name > 0:
            oa_name = oa_name
        else:
            oa_name = ' '
            
        if oa_mobile_no:
            oa_mobile_no = oa_mobile_no.encode('utf-8')
        else:
            oa_mobile_no = ' '
                
        template_sms = u'%s ถึง:%s ติดต่อ:%s โทร:%s' % (
                        move_obj[0].picking_id.customer_product_id.name,
                        move_obj[0].location_dest_id.name,
                        oa_name,
                        oa_mobile_no )
        template_mobile = move_obj[0].picking_id.oa_mobile_no
        other_mobile = move_obj[0].picking_id.oa_mobile_no2
        #print template_sms
        #print template_sms.encode('utf-16')
        picking_id = move_obj[0].picking_id
        all_complete = False
        for pick in self.pool.get('stock.picking').browse(cr, uid, [picking_id.id]):
            for move in pick.move_lines:
                if move.state == 'arrival':
                    all_complete = True
                else:
                    all_complete = False 
                    break
        if all_complete:
            #print template_sms
            self.log(cr, uid, ids[0], 'sms->oa:'+template_sms)
            if template_sms and template_mobile:
                self.send_sms_to_oa(cr, uid, ids, context, template_mobile, template_sms)
                #if len(template_sms) > 65:
                #    self.send_sms_to_oa(cr, uid, ids, context, template_mobile, template_sms[:65])
                #    self.send_sms_to_oa(cr, uid, ids, context, template_mobile, template_sms[65:])
                #else:
                #    self.send_sms_to_oa(cr, uid, ids, context, template_mobile, template_sms)
            if template_sms and other_mobile:
                self.send_sms_to_oa(cr, uid, ids, context, other_mobile, template_sms)   
                #if len(template_sms) > 65:
                #    self.send_sms_to_oa(cr, uid, ids, context, other_mobile, template_sms[:65])            
                #    self.send_sms_to_oa(cr, uid, ids, context, other_mobile, template_sms[65:])            
                #else:
                #    self.send_sms_to_oa(cr, uid, ids, context, other_mobile, template_sms)            
        return []

    def send_sms_to_oa(self, cr, uid, ids, context, mobile_to, text, sender_name='SMS', schedule='', force='standard'):
        import urllib
        host_ids = self.pool.get('omg.configuration').search(cr, uid, [('type','=','sms')])
        #url = "http://www.thaibulksms.com/sms_api.php"
        enable = False
        if host_ids:
            host_obj = self.pool.get('omg.configuration').browse(cr, uid, host_ids)[0]
            url = host_obj['host']
            user = host_obj['username']
            password = host_obj['password']
            enable = host_obj['enable']
        if url and user and password and enable:    
            #thaibulksms    
            #params = urllib.urlencode({'username': user, 'password': password, 'msisdn': mobile_to,
            #                           'message': tools.ustr(text),
            #                           'sender': sender_name, 'ScheduledDelivery':schedule,'force':force})
            if mobile_to:
                mobile_to = re.sub(r'\D',"",mobile_to)
                #mobile_to = mobile_to.replace(' ','').replace('-','').replace('.','')
            if mobile_to and mobile_to[0:1] == '0' and len(mobile_to) == 10:
                mobile_to = '66'+mobile_to[1:len(mobile_to)]
                params = {'CMD':'SENDMSG','FROM':user,'TO':mobile_to,
                    'REPORT':'Y','CHARGE':'Y','CODE':password,'CTYPE':'UNICODE','CONTENT':toHex(text)}
                #str_mp3_data = {}
                #for k, v in params.iteritems():
                #    str_mp3_data[k] = unicode(v).encode('utf-16')
                #data = urllib.urlencode(params)
                #f = urllib.urlopen(url, params)     
                PORT = 3714              # The same port as used by the server
                s = None
                for res in socket.getaddrinfo(url, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM):
                    af, socktype, proto, canonname, sa = res
                    try:
                        s = socket.socket(af, socktype, proto)
                    except socket.error, msg:
                        s = None
                        continue
                    try:
                        s.connect(sa)
                    except socket.error, msg:
                        s.close()
                        s = None
                        continue
                    break
                if s is None:
                    print 'could not open socket'
                    sys.exit(1)
                data = "CMD=SENDMSG&FROM="+user+"&TO="+mobile_to+"&REPORT=Y&CHARGE=Y&CODE="+password+"&CTYPE=UNICODE&CONTENT="+toHex(text)
                length = len(data)
                package = "POST / HTTP/1.1\r\nContent-type:application/x-www-form-urlencoded\r\nContent-length: %d\r\n\r\n%s" % (length,data)
                s.send(package)
                data = s.recv(1024)
                s.close()
                print repr(data)
                       
        return True

    def action_complete(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'date_completed': time.strftime('%Y-%m-%d %H:%M:%S'),'state':'complete'})
        return []

    def action_complete2(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'date_forced': time.strftime('%Y-%m-%d %H:%M:%S'), 'user_forced':uid, 'state':'complete2'})
        return []

    def action_return_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'date_arrival': False,'date_completed':False, 'state':'done'})
        return []

    def action_return_arrival(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'date_completed':False, 'state':'arrival'})
        return []
    
    #POP-008
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if not isinstance(ids, (list)):
            do_ids = [ids]
        else:
            do_ids = ids
        move_obj = self.pool.get('stock.move').browse(cr, uid, do_ids)
        if move_obj:
            if move_obj[0].state == 'done' and 'product_qty' in vals :
                raise osv.except_osv(_('Error'), _('Stock Move Locked -> '+move_obj[0].product_id.name+'.' ))
        return super(stock_move, self).write(cr, uid, ids, vals, context=context)

stock_move()

class stock_picking(osv.osv):

    def _get_date_period_start(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.period_id:
                res[line.id] = line.period_id.date_start
        return res

    def _get_warehouse_lock(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.period_id:
                res[line.id] = line.period_id.warehouse_lock
        return res

    _name = "stock.picking"
    _description = "OMG Picking List"
    _inherit = "stock.picking"

    _columns = {
        'period_id': fields.many2one('omg.sale.period','Period', ondelete='restrict'),
        'customer_product_id': fields.many2one('product.product', 'Customer Product', ondelete='restrict' ),
        'oa_contact_name': fields.char('OA Name',size=100),
        'oa_mobile_no': fields.char('Mobile No', size=20),
        'oa_mobile_no2': fields.char('Other Mobile No', size=20),
        'customer_id': fields.many2one('res.partner', 'Customer', ondelete='restrict'),
        'date_arrival': fields.date('Arrival Date'),
        'date_period_start': fields.function(_get_date_period_start, method=True, type='datetime', string='Period Date'),
        'sms_audit': fields.boolean('Send SMS Audit'),
        'path': fields.char('Logistic Path', size=100),
        'location_store_id': fields.many2one('stock.location', 'Store', ondelete='restrict'),
        'sms_text': fields.char('SMS Text', size=128),
        'warehouse_lock': fields.function(_get_warehouse_lock, method=True, type='boolean', string="Lock"),
    }
    
    _defaults = {
        'sms_audit': False,
    }

    #POP-003
    def copy(self, cr, uid, id, default={}, context=None):
        default.update({
            'state': 'draft',
            'ineco_delivery_date': False,
            'ineco_logistic_path': False,
            'path': False,
            'date_arrival': False,
            'sale_id': False,
            'location_store_id': False,
            'date_done': False,
        })
        return super(stock_picking, self).copy(cr, uid, id, default, context=context)
    
    def schedule_sms(self, cr, uid, context=None):
        cr.execute('select distinct c.id, e.name as customer_product, f.name as location, d.mobile from stock_move a ' \
            'join product_product b on b.id = a.product_id and b.audit = true ' \
            'join stock_picking c on a.picking_id = c.id and sms_audit = false ' \
            'join res_partner_address d on c.address_id = d.id ' \
            'join product_template e on c.customer_product_id = e.id ' \
            'join stock_location f on a.location_dest_id = f.id ' \
            'join omg_sale_period g on c.period_id = g.id and g.date_start::date + 4 = now()::date')
        dict1 = cr.dictfetchall()
        for row in dict1:
            cr.execute('update stock_picking set sms_audit = true where id = %s', (str(row['id']),))
            template_sms = u'โปรโมชั่น:%s ที่:%s ตรวจสอบติดตั้งด้วย' % (
                row['customer_product'].encode('utf-8') , 
                row['location'].encode('utf-8'))
            #print template_sms
            self.send_sms_to_store(cr, uid, row['id'], context, row['mobile'], template_sms)
            self.log(cr, uid, row['id'], 'sms->store:'+template_sms)
    
    def action_done(self, cr, uid, ids, context=None ):
        #self.write(cr, uid, ids, {'state': 'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S')})
        picking = self.pool.get('stock.picking').browse(cr, uid, ids)
        for pick in picking:
            for move in pick.move_lines:
                if pick.date_arrival:
                    self.pool.get('stock.move').write(cr, uid, [move.id], {'date_arrival_planned': pick.date_arrival})
            if pick.type == 'out':    
                if not pick.date_done:
                    pick.write({'state': 'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S')})
                else:
                    pick.write({'state': 'done'})
            else:
                pick.write({'state': 'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S')})
        for pick in picking:
            if pick.type == 'in':
                if pick.purchase_id and pick.purchase_id.requisition_id:
                    pr = self.pool.get('purchase.requisition').browse(cr, uid, pick.purchase_id.requisition_id.id)
                    if pr: 
                        pr.write({'state':'done'})
            elif pick.type == 'out':
                supplier_loc_ids = self.pool.get('stock.location').search(cr, uid, [('name','=','Suppliers')])
                if supplier_loc_ids:                    
                    for line in pick.move_lines:
                        line.write({'location_id': supplier_loc_ids[0]})
                host_ids = self.pool.get('omg.configuration').search(cr, uid, [('type','=','sms')])
                customer_product = pick.customer_product_id.name
                location_name = pick.move_lines[0].location_dest_id.name
                a_date = pick.date_arrival
                b_date = ""
                if host_ids and customer_product:
                    if pick.period_id:
                        b_date = pick.period_id.date_start
                    #print pick.date_arrival, customer_product, location_name
                    #POP-004
                    template_sms = ''
                    if customer_product and b_date and location_name and a_date:
                        if b_date:
                            template_sms = u"โปรโมชั่น:"+customer_product+ u" เริ่ม:"+b_date+u" ถึง:"+location_name+u" วันที่:"+a_date
                        else:
                            template_sms = u"โปรโมชั่น:"+customer_product+ u" ถึง:"+location_name+u" วันที่:"+a_date
                        
                    if pick.sms_text:
                        template_sms = template_sms + " " + pick.sms_text
                    
                    #print template_sms
                    self.log(cr, uid, ids[0], 'sms->store:'+template_sms)
                    #print template_sms.encode('utf-16')
                    template_mobile = ''
                    if pick.address_id and pick.address_id.mobile:
                        template_mobile = pick.address_id.mobile
                    if template_sms and template_mobile:
                        self.send_sms_to_store(cr, uid, ids, context, template_mobile, template_sms)
                    #if len(template_sms) > 65:
                    #    self.send_sms_to_store(cr, uid, ids, context, template_mobile, template_sms[:65] )
                    #    self.send_sms_to_store(cr, uid, ids, context, template_mobile, template_sms[65:] )
                    #else:
                    #    self.send_sms_to_store(cr, uid, ids, context, template_mobile, template_sms)
        return True
    
    def send_sms_to_store(self, cr, uid, ids, context, mobile_to, text, sender_name='SMS', schedule='', force='standard'):
        import urllib
        host_ids = self.pool.get('omg.configuration').search(cr, uid, [('type','=','sms')])
        #url = "http://www.thaibulksms.com/sms_api.php"
        enable = False
        if host_ids:
            host_obj = self.pool.get('omg.configuration').browse(cr, uid, host_ids)[0]
            url = host_obj['host']
            user = host_obj['username']
            password = host_obj['password']
            enable = host_obj['enable']
        if url and user and password and enable:        
            #params = urllib.urlencode({'username': user, 'password': password, 'msisdn': mobile_to,
            #                           'message': tools.ustr(text),
            #                           'sender': sender_name, 'ScheduledDelivery':schedule,'force':force})
            #f = urllib.urlopen(url+"?"+params)
            
            if mobile_to:
                mobile_to = re.sub(r'\D',"",mobile_to)
                #mobile_to = mobile_to.replace(' ','').replace('-','').replace('.','')
            if mobile_to and mobile_to[0:1] == '0' and len(mobile_to) == 10:
                mobile_to = '66'+mobile_to[1:len(mobile_to)]
                params = {'CMD':'SENDMSG','FROM':user,'TO':mobile_to,
                    'REPORT':'Y','CHARGE':'Y','CODE':password,'CTYPE':'LUNICODE','CONTENT':toHex(text) }
                #str_mp3_data = {}
                #for k, v in params.iteritems():
                #    str_mp3_data[k] = unicode(v).encode('utf-16')
                #data = urllib.urlencode(params)
                #f = urllib.urlopen(url, data)
                #HOST = '203.170.228.190'    # The remote host #203.170.230.170, p: 202.149.24.92
                PORT = 3714              # The same port as used by the server
                s = None
                for res in socket.getaddrinfo(url, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM):
                    af, socktype, proto, canonname, sa = res
                    try:
                        s = socket.socket(af, socktype, proto)
                    except socket.error, msg:
                        s = None
                        continue
                    try:
                        s.connect(sa)
                    except socket.error, msg:
                        s.close()
                        s = None
                        continue
                    break
                if s is None:
                    print 'could not open socket'
                    sys.exit(1)
                data = "CMD=SENDMSG&FROM="+user+"&TO="+mobile_to+"&REPORT=Y&CHARGE=Y&CODE="+password+"&CTYPE=UNICODE&CONTENT="+toHex(text)
                length = len(data)
                package = "POST / HTTP/1.1\r\nContent-type:application/x-www-form-urlencoded\r\nContent-length: %d\r\n\r\n%s" % (length,data)
                s.send(package)
                data = s.recv(1024)
                s.close()
                
                #print f.read()            
        return True

    def allow_cancel(self, cr, uid, ids, context=None):
        for pick in self.browse(cr, uid, ids, context=context):
            if not pick.move_lines:
                return True
            for move in pick.move_lines:
                if move.state == 'done':
                    print 'You cannot cancel picking because stock move is in done state !'
                    #raise osv.except_osv(_('Error'), _('You cannot cancel picking because stock move is in done state !'))
        return True

stock_picking()

class stock_location_line_qty(osv.osv):
    _name = "stock.location.line.qty"
    _description = "Stock Location Qty"
    _columns = {
        'name': fields.char('Description',size=64),
        'location_id': fields.many2one('stock.location','Location',required=True, ondelete='restrict'),
        'categ_id': fields.many2one('product.category','Product Category',required=True, ondelete='restrict'),
        'quantity': fields.integer('Quantity'),
    }
stock_location_line_qty()

class stock_oa_address(osv.osv):
    _name = "stock.oa.address"
    _description = "Address of OA"
    _columns = {
        'name': fields.char('Location',size=100,required=True),
        'address_id': fields.many2one('res.partner.address','OA Address', required=True, ondelete='restrict'),
        'location_id': fields.many2one('stock.location','Location', required=True, ondelete='restrict')
    }
stock_oa_address()

class stock_location_booking(osv.osv):
    _name = "stock.location.booking"
    _description = "Booking Location"
    _columns = {
        'name': fields.char('Description',size=100),
        'product_id': fields.many2one('product.product','Product',required=True, ondelete='restrict'),
        'category_id': fields.many2one('product.category','Category',required=True, ondelete='restrict'),
        #POP-002
        'service_category_id': fields.many2one('product.category','Service Category',required=True, ondelete='restrict'),
        'period_id': fields.many2one('omg.sale.period','Period', required=True, ondelete='restrict'),
        'saleman_id': fields.many2one('res.users', 'Salesman', ondelete='restrict'),
        'date_booking': fields.date('Booking Date', required=True),
        'group_id': fields.many2one('omg.sale.location.group', 'Group', required=True, ondelete='restrict'),
        'chain_id': fields.many2one('omg.sale.chain', 'Chain', required=True, ondelete='restrict'),
        'location_id': fields.many2one('stock.location','Location', required=True, ondelete='restrict'),
        'contact_id': fields.many2one('omg.sale.reserve.contact', 'Contact', required=True, ondelete='restrict'),
        'contact_line_id': fields.many2one('omg.sale.reserve.contact.line','Contact Line', required=True, ondelete="cascade"),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('booking', 'Booking'),
            ('done', 'Done'),
            ('cancel', 'Cancel'),
            ], 'State', readonly=True),
        'order_id': fields.many2one('sale.order','Sale Order'),
        'group_special_id': fields.many2one('omg.sale.group.special', 'Group Special'),
        'ineco_check_place': fields.boolean('Check Place'),
    }
    _order = "date_booking"
    _defaults = {
        'name': '...',
        'state': 'draft',
        'date_booking': lambda *a: time.strftime('%Y-%m-%d'),
        'saleman_id': lambda self, cr, uid, context: uid,
        'ineco_check_place': True,
    }
stock_location_booking()

class ineco_stock_location_category_max(osv.osv):
    _name = "ineco.stock.location.category.max"
    _description = "Maximum Category per Location"
    _columns = {
        'name': fields.char('Description', size=100),
        'category_id': fields.many2one('product.category', 'Category', required=True),
        'location_id': fields.many2one('stock.location', 'Location'),
        'quantity': fields.integer('Max Place', required=True),
    }
    _defaults = {
        'quantity': 1
    }
ineco_stock_location_category_max()


class stock_location(osv.osv):
    _name = "stock.location"
    _inherit = "stock.location"
    _description = "Stock extended of Location"
    _columns = {
        'lineqty_ids': fields.one2many('stock.location.line.qty', 'location_id', 'Line Qty'),
        'oa_address_ids': fields.one2many('stock.oa.address', 'location_id', 'OA Address Line'),
        'booking_ids': fields.one2many('stock.location.booking', 'location_id', 'Booking Line'),
        'max_place_qty': fields.integer("Maximum Place Count"),
        'store_code': fields.char('Store Code', size=20),
        'name_thai': fields.char('Name Thai', size=240),
        'path': fields.char('Path Detail', size=240),
        'store_address_id': fields.many2one('res.partner.address','Store Contact', ondelete='restrict'),
        'omg_approve': fields.boolean('Approve'),
        'max_category_ids': fields.one2many('ineco.stock.location.category.max', 'location_id', 'Category Capacity'),
        'omg_no': fields.char('No', size=100),
        'omg_classification': fields.char('Classification', size=100),
        'omg_format': fields.char('Format', size=100),
        'omg_size': fields.char('Size', size=100),
        'omg_no': fields.char('No', size=100),
        'omg_demo': fields.char('Demo', size=100),
        'omg_roaming': fields.char('Roaming', size=100),
        'omg_ufo': fields.char('UFO', size=100),
        'omg_kvillage': fields.char('K-Village', size=100),
        'omg_marketplace': fields.char('Market Place', size=100),
        'omg_foodhall': fields.char('Food Hall', size=100),
        'omg_total': fields.char('Total', size=100),
        'omg_remark': fields.char('Remark', size=100),
        'omg_dymilk7': fields.char('D/Y Milk7', size=100),
        'omg_dymilk3': fields.char('D/y Milk3', size=100),
        'omg_cerial7': fields.char('Cerial7', size=100),
        'omg_cerial3': fields.char('Cerial3', size=100),
        'omg_cy7': fields.char('C/Y 7', size=100),
        'omg_cy3': fields.char('C/Y 3', size=100),
        'omg_fruitjuice7': fields.char('Fruit Juice 7', size=100),
        'omg_fruitjuice3': fields.char('Fruit Juice 3', size=100),
        'omg_noodle7': fields.char('Noodle 7', size=100),
        'omg_noodle3': fields.char('Noodle 3', size=100),
        'omg_milkpowder7': fields.char('Milk Powder 7', size=100),
        'omg_milkpowder3': fields.char('Milk Powder 3', size=100),
        'omg_cooking7': fields.char('Cooking 7', size=100),
        'omg_cooking3': fields.char('Cooking 3', size=100),
        'omg_snack7': fields.char('Snack 7', size=100),
        'omg_snack3': fields.char('Snack 3', size=100),
        'omg_coffee7': fields.char('Coffee 7', size=100),
        'omg_coffee3': fields.char('Coffee 3', size=100),
        'omg_icecoffee7': fields.char('Ice Coffee 7', size=100),
        'omg_icecoffee3': fields.char('Ice Coffee 3', size=100),
        'omg_personalcare7': fields.char('Personal Care 7', size=100),
        'omg_personalcare3': fields.char('Personal Care 3', size=100),
        'omg_recruiter': fields.char('Recruiter', size=100),
        'omg_accountname': fields.char('Account Name', size=100),
        'omg_accountno': fields.char('Account No', size=100),
        'omg_region': fields.char('Region', size=100),
        'omg_omgarea': fields.char('OMG Area', size=100),
        'omg_latitude': fields.char('Latitude', size=100),
        'omg_longitude': fields.char('Longitude', size=100),
        'omg_channel': fields.char('Channel', size=100),
        'omg_store_code': fields.char('OMG Store Code', size=100),
        'omg_no_other': fields.char('No Other', size=100),
        'omg_retail_store_name': fields.char('Retail Store Name', size=100),
        'omg_concentratedrink7': fields.char('Concentrate Drink 7', size=100),
        'omg_concentratedrink3': fields.char('Concentrate Drink 3', size=100),
        'omg_alway_equipment': fields.boolean('Alway Send Equipment'),
        'mapping_ids': fields.one2many('ineco.stock.location.product.mapping', 'location_id', 'Product Mapping'),
    }
    _defaults = {
        'omg_approve': False,
    }
    
stock_location()

class stock_location_set(osv.osv):
    _name = "stock.location.set"
    _description = "Set of Locations"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'lines' : fields.one2many('stock.location.set.line','location_set_id', 'Location Lines'),
    }
stock_location_set()

class stock_location_set_line(osv.osv):
    _name = "stock.location.set.line"
    _description = "Detail of Location Set"
    _columns = {
        'name': fields.char('Location Name', size=100, required=True),
        'location_set_id': fields.many2one('stock.location.set','Location Set',required=True, ondelete='restrict'),
        'location_id': fields.many2one('stock.location','Location', required=True, ondelete='restrict'),
    }
    _sql_constraints = [
        ('location_id_set_unique', 'unique (location_id,location_set_id)', 'Location must be unique in same location set!')
    ]
    
stock_location_set_line()

class ineco_sms_type(osv.osv):
    _name = "ineco.sms.type"
    _description = "SMS Type"
    _columns = {
        'name': fields.char("Name", size=64, required=True),
        'condition': fields.char("Criteria String", size=64, required=True),
    }
    _sql_constraints = [
        ('sms_condition_unique', 'unique (condition)', 'SMS Crieteria must be unique in same location set!')
    ]
ineco_sms_type()    

#POP-001 -> Move omg.stock
class ineco_query_stock_report(osv.osv):
    _name = 'ineco.query.stock.report'
    _description = 'Final Summary Stock Report'
    _auto = False
    
    def init(self,cr):
        tools.drop_view_if_exists(cr, 'ineco_query_stock_report')
        cr.execute("""
            CREATE OR REPLACE VIEW ineco_query_stock_report AS 
             SELECT pt.name_template AS customer_product_name, pp.name_template AS product_name, spl.name AS production_lot_id, spl.date_expired, st.name AS pack_id, sl.name AS location_id, sp.ineco_delivery_date::timestamp without time zone AS date_expected, pu.name AS uom_name, sm.product_qty, pu2.name AS warehouse_uom_name, ineco_convert_stock(pp.warehouse_uom, sm.product_qty::double precision) AS product_full_qty, sm.product_qty::double precision - ineco_get_stock(pp.warehouse_uom, ineco_convert_stock(pp.warehouse_uom, sm.product_qty::double precision)) AS product_split_qty, issc.name AS sticker_name, pp.warehouse_uom, sp.ineco_delivery_date, sm.product_id as product_id
               FROM stock_move sm
               LEFT JOIN stock_picking sp ON sm.picking_id = sp.id
               LEFT JOIN product_product pp ON sm.product_id = pp.id
               LEFT JOIN product_product pt ON sp.customer_product_id = pt.id
               LEFT JOIN stock_production_lot spl ON sm.prodlot_id = spl.id
               LEFT JOIN stock_tracking st ON sm.tracking_id = st.id
               LEFT JOIN stock_location sl ON sm.location_id = sl.id
               LEFT JOIN product_template ptt ON pp.id = ptt.id
               LEFT JOIN product_uom pu ON ptt.uom_id = pu.id
               LEFT JOIN product_uom pu2 ON pp.warehouse_uom = pu2.id
               LEFT JOIN ineco_stock_sticker_category issc ON pp.sticker_category_id = issc.id
              WHERE sp.type::text = 'out'::text AND sm.state::text <> 'cancel'::text
              ORDER BY pp.sticker_category_id, sl.name, pt.name_template, spl.name DESC, st.name DESC, pp.name_template
        """)
        
ineco_query_stock_report()

#POP-006
class ineco_stock_location_stock_product_mapping(osv.osv):
    _name = 'ineco.stock.location.product.mapping'
    _description = "Stock Location Mapping"
    _columns = {
        'location_id': fields.many2one('stock.location', 'Location'),
        'product_id_from': fields.many2one('product.product', 'From Product', required=True),
        'product_id_to': fields.many2one('product.product','To Product', required=True),
    }
ineco_stock_location_stock_product_mapping()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
