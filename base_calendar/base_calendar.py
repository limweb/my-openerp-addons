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

from datetime import datetime, timedelta, date
from dateutil import parser
from dateutil import rrule
from osv import fields, osv
from service import web_services
from tools.translate import _
import pytz
import re
import time
import tools

months = {
    1: "January", 2: "February", 3: "March", 4: "April", \
    5: "May", 6: "June", 7: "July", 8: "August", 9: "September", \
    10: "October", 11: "November", 12: "December"
}

def get_recurrent_dates(rrulestring, exdate, startdate=None, exrule=None):
    """
    Get recurrent dates based on Rule string considering exdate and start date
    @param rrulestring: Rulestring
    @param exdate: List of exception dates for rrule
    @param startdate: Startdate for computing recurrent dates
    @return: List of Recurrent dates
    """
    def todate(date):
        val = parser.parse(''.join((re.compile('\d')).findall(date)))
        return val

    if not startdate:
        startdate = datetime.now()
    if not exdate:
        exdate = []
    rset1 = rrule.rrulestr(str(rrulestring), dtstart=startdate, forceset=True)

    for date in exdate:
        datetime_obj = todate(date)
        rset1._exdate.append(datetime_obj)
    if exrule:
        rset1.exrule(rrule.rrulestr(str(exrule), dtstart=startdate))

    return list(rset1._iter())

def base_calendar_id2real_id(base_calendar_id=None, with_date=False):
    """
    This function converts virtual event id into real id of actual event
    @param base_calendar_id: Id of calendar
    @param with_date: If value passed to this param it will return dates based on value of withdate + base_calendar_id
    """

    if base_calendar_id and isinstance(base_calendar_id, (str, unicode)):
        res = base_calendar_id.split('-')

        if len(res) >= 2:
            real_id = res[0]
            if with_date:
                real_date = time.strftime("%Y-%m-%d %H:%M:%S", \
                                 time.strptime(res[1], "%Y%m%d%H%M%S"))
                start = datetime.strptime(real_date, "%Y-%m-%d %H:%M:%S")
                end = start + timedelta(hours=with_date)
                return (int(real_id), real_date, end.strftime("%Y-%m-%d %H:%M:%S"))
            return int(real_id)

    return base_calendar_id and int(base_calendar_id) or base_calendar_id

def real_id2base_calendar_id(real_id, recurrent_date):
    """
    Convert  real id of record into virtual id using recurrent_date
    e.g. real id is 1 and recurrent_date is 01-12-2009 10:00:00 then it will return
        1-20091201100000
    @return: real id with recurrent date.
    """

    if real_id and recurrent_date:
        recurrent_date = time.strftime("%Y%m%d%H%M%S", \
                            time.strptime(recurrent_date, "%Y-%m-%d %H:%M:%S"))
        return '%d-%s' % (real_id, recurrent_date)
    return real_id

def _links_get(self, cr, uid, context=None):
    """
    Get request link.
    @param cr: the current row, from the database cursor,
    @param uid: the current user’s ID for security checks,
    @param context: A standard dictionary for contextual values
    @return: list of dictionary which contain object and name and id.
    """
    obj = self.pool.get('res.request.link')
    ids = obj.search(cr, uid, [])
    res = obj.read(cr, uid, ids, ['object', 'name'], context=context)
    return [(r['object'], r['name']) for r in res]

html_invitation = """
<html>
<head>
<meta http-equiv="Content-type" content="text/html; charset=utf-8" />
<title>%(name)s</title>
</head>
<body>
<table border="0" cellspacing="10" cellpadding="0" width="100%%"
    style="font-family: Arial, Sans-serif; font-size: 14">
    <tr>
        <td width="100%%">Hello,</td>
    </tr>
    <tr>
        <td width="100%%">You are invited for <i>%(company)s</i> Event.</td>
    </tr>
    <tr>
        <td width="100%%">Below are the details of event:</td>
    </tr>
</table>

<table cellspacing="0" cellpadding="5" border="0" summary=""
    style="width: 90%%; font-family: Arial, Sans-serif; border: 1px Solid #ccc; background-color: #f6f6f6">
    <tr valign="center" align="center">
        <td bgcolor="DFDFDF">
        <h3>%(name)s</h3>
        </td>
    </tr>
    <tr>
        <td>
        <table cellpadding="8" cellspacing="0" border="0"
            style="font-size: 14" summary="Eventdetails" bgcolor="f6f6f6"
            width="90%%">
            <tr>
                <td width="21%%">
                <div><b>Start Date</b></div>
                </td>
                <td><b>:</b></td>
                <td>%(start_date)s</td>
                <td width="15%%">
                <div><b>End Date</b></div>
                </td>
                <td><b>:</b></td>
                <td width="25%%">%(end_date)s</td>
            </tr>
            <tr valign="top">
                <td><b>Description</b></td>
                <td><b>:</b></td>
                <td colspan="3">%(description)s</td>
            </tr>
            <tr valign="top">
                <td>
                <div><b>Location</b></div>
                </td>
                <td><b>:</b></td>
                <td colspan="3">%(location)s</td>
            </tr>
            <tr valign="top">
                <td>
                <div><b>Event Attendees</b></div>
                </td>
                <td><b>:</b></td>
                <td colspan="3">
                <div>
                <div>%(attendees)s</div>
                </div>
                </td>
            </tr>
        </table>
        </td>
    </tr>
</table>
<table border="0" cellspacing="10" cellpadding="0" width="100%%"
    style="font-family: Arial, Sans-serif; font-size: 14">
    <tr>
        <td width="100%%">From:</td>
    </tr>
    <tr>
        <td width="100%%">%(user)s</td>
    </tr>
    <tr valign="top">
        <td width="100%%">-<font color="a7a7a7">-------------------------</font></td>
    </tr>
    <tr>
        <td width="100%%"> <font color="a7a7a7">%(sign)s</font></td>
    </tr>
</table>
</body>
</html>
"""

class calendar_attendee(osv.osv):
    """
    Calendar Attendee Information
    """
    _name = 'calendar.attendee'
    _description = 'Attendee information'
    _rec_name = 'cutype'

    __attribute__ = {}

    def _get_address(self, name=None, email=None):
        """
        Gives email information in ical CAL-ADDRESS type format
        @param name: Name for CAL-ADDRESS value
        @param email: Email address for CAL-ADDRESS value
        """
        if name and email:
            name += ':'
        return (name or '') + (email and ('MAILTO:' + email) or '')

    def _compute_data(self, cr, uid, ids, name, arg, context=None):
        """
        Compute data on function fields for attendee values .
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of calendar attendee’s IDs.
        @param name: name of field.
        @param context: A standard dictionary for contextual values
        @return: Dictionary of form {id: {'field Name': value'}}.
        """
        name = name[0]
        result = {}
        for attdata in self.browse(cr, uid, ids, context=context):
            id = attdata.id
            result[id] = {}
            if name == 'sent_by':
                if not attdata.sent_by_uid:
                    result[id][name] = ''
                    continue
                else:
                    result[id][name] = self._get_address(attdata.sent_by_uid.name, \
                                        attdata.sent_by_uid.address_id.email)

            if name == 'cn':
                if attdata.user_id:
                    result[id][name] = attdata.user_id.name
                elif attdata.partner_address_id:
                    result[id][name] = attdata.partner_address_id.name or attdata.partner_id.name
                else:
                    result[id][name] = attdata.email or ''

            if name == 'delegated_to':
                todata = []
                for child in attdata.child_ids:
                    if child.email:
                        todata.append('MAILTO:' + child.email)
                result[id][name] = ', '.join(todata)

            if name == 'delegated_from':
                fromdata = []
                for parent in attdata.parent_ids:
                    if parent.email:
                        fromdata.append('MAILTO:' + parent.email)
                result[id][name] = ', '.join(fromdata)

            if name == 'event_date':
                if attdata.ref:
                    result[id][name] = attdata.ref.date
                else:
                    result[id][name] = False

            if name == 'event_end_date':
                if attdata.ref:
                    result[id][name] = attdata.ref.date_deadline
                else:
                    result[id][name] = False

            if name == 'sent_by_uid':
                if attdata.ref:
                    result[id][name] = (attdata.ref.user_id.id, attdata.ref.user_id.name)
                else:
                    result[id][name] = uid

            if name == 'language':
                user_obj = self.pool.get('res.users')
                lang = user_obj.read(cr, uid, uid, ['context_lang'], context=context)['context_lang']
                result[id][name] = lang.replace('_', '-')

        return result

    def _links_get(self, cr, uid, context=None):
        """
        Get request link for ref field in calendar attendee.
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param context: A standard dictionary for contextual values
        @return: list of dictionary which contain object and name and id.
        """
        obj = self.pool.get('res.request.link')
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ['object', 'name'], context=context)
        return [(r['object'], r['name']) for r in res]

    def _lang_get(self, cr, uid, context=None):
        """
        Get language for language selection field.
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param context: A standard dictionary for contextual values
        @return: list of dictionary which contain code and name and id.
        """
        obj = self.pool.get('res.lang')
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ['code', 'name'], context=context)
        res = [((r['code']).replace('_', '-').lower(), r['name']) for r in res]
        return res

    _columns = {
        'cutype': fields.selection([('individual', 'Individual'), \
                    ('group', 'Group'), ('resource', 'Resource'), \
                    ('room', 'Room'), ('unknown', 'Unknown') ], \
                    'Invite Type', help="Specify the type of Invitation"),
        'member': fields.char('Member', size=124,
                    help="Indicate the groups that the attendee belongs to"),
        'role': fields.selection([('req-participant', 'Participation required'), \
                    ('chair', 'Chair Person'), \
                    ('opt-participant', 'Optional Participation'), \
                    ('non-participant', 'For information Purpose')], 'Role', \
                    help='Participation role for the calendar user'),
        'state': fields.selection([('tentative', 'Tentative'),
                        ('needs-action', 'Needs Action'),
                        ('accepted', 'Accepted'),
                        ('declined', 'Declined'),
                        ('delegated', 'Delegated')], 'State', readonly=True, \
                        help="Status of the attendee's participation"),
        'rsvp':  fields.boolean('Required Reply?',
                    help="Indicats whether the favor of a reply is requested"),
        'delegated_to': fields.function(_compute_data, method=True, \
                string='Delegated To', type="char", size=124, store=True, \
                multi='delegated_to', help="The users that the original \
request was delegated to"),
        'delegated_from': fields.function(_compute_data, method=True, string=\
            'Delegated From', type="char", store=True, size=124, multi='delegated_from'),
        'parent_ids': fields.many2many('calendar.attendee', 'calendar_attendee_parent_rel', \
                                    'attendee_id', 'parent_id', 'Delegrated From'),
        'child_ids': fields.many2many('calendar.attendee', 'calendar_attendee_child_rel', \
                                      'attendee_id', 'child_id', 'Delegrated To'),
        'sent_by': fields.function(_compute_data, method=True, string='Sent By', \
                        type="char", multi='sent_by', store=True, size=124, \
                        help="Specify the user that is acting on behalf of the calendar user"),
        'sent_by_uid': fields.function(_compute_data, method=True, string='Sent By User', \
                            type="many2one", relation="res.users", multi='sent_by_uid'),
        'cn': fields.function(_compute_data, method=True, string='Common name', \
                            type="char", size=124, multi='cn', store=True),
        'dir': fields.char('URI Reference', size=124, help="Reference to the URI\
that points to the directory information corresponding to the attendee."),
        'language': fields.function(_compute_data, method=True, string='Language', \
                    type="selection", selection=_lang_get, multi='language', \
                    store=True, help="To specify the language for text values in a\
property or property parameter."),
        'user_id': fields.many2one('res.users', 'User'),
        'partner_address_id': fields.many2one('res.partner.address', 'Contact'),
        'partner_id': fields.related('partner_address_id', 'partner_id', type='many2one', \
                        relation='res.partner', string='Partner', help="Partner related to contact"),
        'email': fields.char('Email', size=124, help="Email of Invited Person"),
        'event_date': fields.function(_compute_data, method=True, string='Event Date', \
                            type="datetime", multi='event_date'),
        'event_end_date': fields.function(_compute_data, method=True, \
                            string='Event End Date', type="datetime", \
                            multi='event_end_date'),
        'ref': fields.reference('Event Ref', selection=_links_get, size=128),
        'availability': fields.selection([('free', 'Free'), ('busy', 'Busy')], 'Free/Busy', readonly="True"),
     }
    _defaults = {
        'state': 'needs-action',
        'role': 'req-participant',
        'rsvp':  True,
        'cutype': 'individual',
    }

    def copy(self, cr, uid, id, default=None, context=None):
        raise osv.except_osv(_('Warning!'), _('Can not Duplicate'))

    def get_ics_file(self, cr, uid, event_obj, context=None):
        """
        Returns iCalendar file for the event invitation
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param event_obj: Event object (browse record)
        @param context: A standard dictionary for contextual values
        @return: .ics file content
        """
        res = None
        def ics_datetime(idate, short=False):
            if idate:
                if short or len(idate)<=10:
                    return date.fromtimestamp(time.mktime(time.strptime(idate, '%Y-%m-%d')))
                else:
                    return datetime.strptime(idate, '%Y-%m-%d %H:%M:%S')
            else:
                return False
        try:
            # FIXME: why isn't this in CalDAV?
            import vobject
        except ImportError:
            return res
        cal = vobject.iCalendar()
        event = cal.add('vevent')
        if not event_obj.date_deadline or not event_obj.date:
              raise osv.except_osv(_('Warning !'),_("Couldn't Invite because date is not specified!"))     
        event.add('created').value = ics_datetime(time.strftime('%Y-%m-%d %H:%M:%S'))
        event.add('dtstart').value = ics_datetime(event_obj.date)
        event.add('dtend').value = ics_datetime(event_obj.date_deadline)
        event.add('summary').value = event_obj.name
        if  event_obj.description:
            event.add('description').value = event_obj.description
        if event_obj.location:
            event.add('location').value = event_obj.location
        if event_obj.rrule:
            event.add('rrule').value = event_obj.rrule
        if event_obj.organizer:
            event_org = event.add('organizer')
            event_org.params['CN'] = [event_obj.organizer]
            event_org.value = 'MAILTO:' + (event_obj.organizer)
        elif event_obj.user_id or event_obj.organizer_id:
            event_org = event.add('organizer')
            organizer = event_obj.organizer_id
            if not organizer:
                organizer = event_obj.user_id
            event_org.params['CN'] = [organizer.name]
            event_org.value = 'MAILTO:' + (organizer.user_email or organizer.name)

        if event_obj.alarm_id:
            # computes alarm data
            valarm = event.add('valarm')
            alarm_object = self.pool.get('res.alarm')
            alarm_data = alarm_object.read(cr, uid, event_obj.alarm_id.id, context=context)
            # Compute trigger data
            interval = alarm_data['trigger_interval']
            occurs = alarm_data['trigger_occurs']
            duration = (occurs == 'after' and alarm_data['trigger_duration']) \
                                            or -(alarm_data['trigger_duration'])
            related = alarm_data['trigger_related']
            trigger = valarm.add('TRIGGER')
            trigger.params['related'] = [related.upper()]
            if interval == 'days':
                delta = timedelta(days=duration)
            if interval == 'hours':
                delta = timedelta(hours=duration)
            if interval == 'minutes':
                delta = timedelta(minutes=duration)
            trigger.value = delta
            # Compute other details
            valarm.add('DESCRIPTION').value = alarm_data['name'] or 'OpenERP'
                
        for attendee in event_obj.attendee_ids:
            attendee_add = event.add('attendee')
            attendee_add.params['CUTYPE'] = [str(attendee.cutype)]
            attendee_add.params['ROLE'] = [str(attendee.role)]
            attendee_add.params['RSVP'] = [str(attendee.rsvp)]
            attendee_add.value = 'MAILTO:' + (attendee.email or '')
        res = cal.serialize()
        return res

    def _send_mail(self, cr, uid, ids, mail_to, email_from=tools.config.get('email_from', False), context=None):
        """
        Send mail for event invitation to event attendees.
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of attendee’s IDs.
        @param email_from: Email address for user sending the mail
        @param context: A standard dictionary for contextual values
        @return: True
        """
        if context is None:
            context = {}

        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.name
        for att in self.browse(cr, uid, ids, context=context):
            sign = att.sent_by_uid and att.sent_by_uid.signature or ''
            sign = '<br>'.join(sign and sign.split('\n') or [])
            res_obj = att.ref
            if res_obj:
                att_infos = []
                sub = res_obj.name
                other_invitation_ids = self.search(cr, uid, [('ref', '=', res_obj._name + ',' + str(res_obj.id))])

                for att2 in self.browse(cr, uid, other_invitation_ids):
                    att_infos.append(((att2.user_id and att2.user_id.name) or \
                                 (att2.partner_id and att2.partner_id.name) or \
                                    att2.email) + ' - Status: ' + att2.state.title())
                body_vals = {'name': res_obj.name,
                            'start_date': res_obj.date,
                            'end_date': res_obj.date_deadline or False,
                            'description': res_obj.description or '-',
                            'location': res_obj.location or '-',
                            'attendees': '<br>'.join(att_infos),
                            'user': res_obj.user_id and res_obj.user_id.name or 'OpenERP User',
                            'sign': sign,
                            'company': company
                }
                body = html_invitation % body_vals
                if mail_to and email_from:
                    attach = self.get_ics_file(cr, uid, res_obj, context=context)
                    tools.email_send(
                        email_from,
                        mail_to,
                        sub,
                        body,
                        attach=attach and [('invitation.ics', attach)] or None,
                        subtype='html',
                        reply_to=email_from
                    )
            return True

    def onchange_user_id(self, cr, uid, ids, user_id, *args, **argv):
        """
        Make entry on email and availbility on change of user_id field.
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of calendar attendee’s IDs.
        @param user_id: Changed value of User id
        @return: dictionary of value. which put value in email and availability fields.
        """

        if not user_id:
            return {'value': {'email': ''}}
        usr_obj = self.pool.get('res.users')
        user = usr_obj.browse(cr, uid, user_id, *args)
        return {'value': {'email': user.address_id.email, 'availability':user.availability}}

    def do_tentative(self, cr, uid, ids, context=None, *args):
        """ Makes event invitation as Tentative
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of calendar attendee’s IDs
        @param *args: Get Tupple value
        @param context: A standard dictionary for contextual values
        """
        return self.write(cr, uid, ids, {'state': 'tentative'}, context)

    def do_accept(self, cr, uid, ids, context=None, *args):
        """
        Update state of invitation as Accepted and
        if the invited user is other then event user it will make a copy of this event for invited user
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of calendar attendee’s IDs.
        @param context: A standard dictionary for contextual values
        @return: True
        """
        if context is None:
            context = {}

        for vals in self.browse(cr, uid, ids, context=context):
            if vals.ref and vals.ref.user_id:
                mod_obj = self.pool.get(vals.ref._name)
                defaults = {'user_id': vals.user_id.id, 'organizer_id': vals.ref.user_id.id}
                mod_obj.copy(cr, uid, vals.ref.id, default=defaults, context=context)
            self.write(cr, uid, vals.id, {'state': 'accepted'}, context)

        return True

    def do_decline(self, cr, uid, ids, context=None, *args):
        """ Marks event invitation as Declined
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of calendar attendee’s IDs
        @param *args: Get Tupple value
        @param context: A standard dictionary for contextual values """
        if context is None:
            context = {}
        return self.write(cr, uid, ids, {'state': 'declined'}, context)

    def create(self, cr, uid, vals, context=None):
        """ Overrides orm create method.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param vals: Get Values
        @param context: A standard dictionary for contextual values """

        if context is None:
            context = {}
        if not vals.get("email") and vals.get("cn"):
            cnval = vals.get("cn").split(':')
            email = filter(lambda x:x.__contains__('@'), cnval)
            vals['email'] = email and email[0] or ''
            vals['cn'] = vals.get("cn")
        res = super(calendar_attendee, self).create(cr, uid, vals, context)
        return res
calendar_attendee()

class res_alarm(osv.osv):
    """Resource Alarm """
    _name = 'res.alarm'
    _description = 'Basic Alarm Information'

    _columns = {
        'name':fields.char('Name', size=256, required=True),
        'trigger_occurs': fields.selection([('before', 'Before'), \
                                            ('after', 'After')], \
                                        'Triggers', required=True),
        'trigger_interval': fields.selection([('minutes', 'Minutes'), \
                                                ('hours', 'Hours'), \
                                                ('days', 'Days')], 'Interval', \
                                                required=True),
        'trigger_duration': fields.integer('Duration', required=True),
        'trigger_related': fields.selection([('start', 'The event starts'), \
                                            ('end', 'The event ends')], \
                                            'Related to', required=True),
        'duration': fields.integer('Duration', help="""Duration' and 'Repeat' \
are both optional, but if one occurs, so MUST the other"""),
        'repeat': fields.integer('Repeat'),
        'active': fields.boolean('Active', help="If the active field is set to \
true, it will allow you to hide the event alarm information without removing it.")
    }
    _defaults = {
        'trigger_interval': 'minutes',
        'trigger_duration': 5,
        'trigger_occurs': 'before',
        'trigger_related': 'start',
        'active': 1,
    }

    def do_alarm_create(self, cr, uid, ids, model, date, context=None):
        """
        Create Alarm for event.
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of res alarm’s IDs.
        @param model: Model name.
        @param date: Event date
        @param context: A standard dictionary for contextual values
        @return: True
        """
        if context is None:
            context = {}
        alarm_obj = self.pool.get('calendar.alarm')
        res_alarm_obj = self.pool.get('res.alarm')
        ir_obj = self.pool.get('ir.model')
        model_id = ir_obj.search(cr, uid, [('model', '=', model)])[0]

        model_obj = self.pool.get(model)
        for data in model_obj.browse(cr, uid, ids, context=context):

            basic_alarm = data.alarm_id
            cal_alarm = data.base_calendar_alarm_id
            if (not basic_alarm and cal_alarm) or (basic_alarm and cal_alarm):
                new_res_alarm = None
                # Find for existing res.alarm
                duration = cal_alarm.trigger_duration
                interval = cal_alarm.trigger_interval
                occurs = cal_alarm.trigger_occurs
                related = cal_alarm.trigger_related
                domain = [('trigger_duration', '=', duration), ('trigger_interval', '=', interval), ('trigger_occurs', '=', occurs), ('trigger_related', '=', related)]
                alarm_ids = res_alarm_obj.search(cr, uid, domain, context=context)
                if not alarm_ids:
                    val = {
                            'trigger_duration': duration,
                            'trigger_interval': interval,
                            'trigger_occurs': occurs,
                            'trigger_related': related,
                            'name': str(duration) + ' ' + str(interval) + ' '  + str(occurs)
                           }
                    new_res_alarm = res_alarm_obj.create(cr, uid, val, context=context)
                else:
                    new_res_alarm = alarm_ids[0]
                cr.execute('UPDATE %s ' % model_obj._table + \
                            ' SET base_calendar_alarm_id=%s, alarm_id=%s ' \
                            ' WHERE id=%s', 
                            (cal_alarm.id, new_res_alarm, data.id))

            self.do_alarm_unlink(cr, uid, [data.id], model)
            if basic_alarm:
                vals = {
                    'action': 'display',
                    'description': data.description,
                    'name': data.name,
                    'attendee_ids': [(6, 0, map(lambda x:x.id, data.attendee_ids))],
                    'trigger_related': basic_alarm.trigger_related,
                    'trigger_duration': basic_alarm.trigger_duration,
                    'trigger_occurs': basic_alarm.trigger_occurs,
                    'trigger_interval': basic_alarm.trigger_interval,
                    'duration': basic_alarm.duration,
                    'repeat': basic_alarm.repeat,
                    'state': 'run',
                    'event_date': data[date],
                    'res_id': data.id,
                    'model_id': model_id,
                    'user_id': uid
                 }
                alarm_id = alarm_obj.create(cr, uid, vals)
                cr.execute('UPDATE %s ' % model_obj._table + \
                            ' SET base_calendar_alarm_id=%s, alarm_id=%s '
                            ' WHERE id=%s', \
                            ( alarm_id, basic_alarm.id, data.id) )
        return True

    def do_alarm_unlink(self, cr, uid, ids, model, context=None):
        """
        Delete alarm specified in ids
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of res alarm’s IDs.
        @param model: Model name for which alarm is to be cleared.
        @return: True
        """
        if context is None:
            context = {}
        alarm_obj = self.pool.get('calendar.alarm')
        ir_obj = self.pool.get('ir.model')
        model_id = ir_obj.search(cr, uid, [('model', '=', model)])[0]
        model_obj = self.pool.get(model)
        for datas in model_obj.browse(cr, uid, ids, context=context):
            alarm_ids = alarm_obj.search(cr, uid, [('model_id', '=', model_id), ('res_id', '=', datas.id)])
            if alarm_ids:
                alarm_obj.unlink(cr, uid, alarm_ids)
                cr.execute('Update %s set base_calendar_alarm_id=NULL, alarm_id=NULL\
                            where id=%%s' % model_obj._table,(datas.id,))
        return True

res_alarm()

class calendar_alarm(osv.osv):
    _name = 'calendar.alarm'
    _description = 'Event alarm information'
    _inherit = 'res.alarm'
    __attribute__ = {}

    _columns = {
        'alarm_id': fields.many2one('res.alarm', 'Basic Alarm', ondelete='cascade'),
        'name': fields.char('Summary', size=124, help="""Contains the text to be \
                     used as the message subject for email \
                     or contains the text to be used for display"""),
        'action': fields.selection([('audio', 'Audio'), ('display', 'Display'), \
                ('procedure', 'Procedure'), ('email', 'Email') ], 'Action', \
                required=True, help="Defines the action to be invoked when an alarm is triggered"),
        'description': fields.text('Description', help='Provides a more complete \
                            description of the calendar component, than that \
                            provided by the "SUMMARY" property'),
        'attendee_ids': fields.many2many('calendar.attendee', 'alarm_attendee_rel', \
                                      'alarm_id', 'attendee_id', 'Attendees', readonly=True),
        'attach': fields.binary('Attachment', help="""* Points to a sound resource,\
                     which is rendered when the alarm is triggered for audio,
                    * File which is intended to be sent as message attachments for email,
                    * Points to a procedure resource, which is invoked when\
                      the alarm is triggered for procedure."""),
        'res_id': fields.integer('Resource ID'),
        'model_id': fields.many2one('ir.model', 'Model'),
        'user_id': fields.many2one('res.users', 'Owner'),
        'event_date': fields.datetime('Event Date'),
        'event_end_date': fields.datetime('Event End Date'),
        'trigger_date': fields.datetime('Trigger Date', readonly="True"),
        'state':fields.selection([
                    ('draft', 'Draft'),
                    ('run', 'Run'),
                    ('stop', 'Stop'),
                    ('done', 'Done'),
                ], 'State', select=True, readonly=True),
     }

    _defaults = {
        'action': 'email',
        'state': 'run',
     }

    def create(self, cr, uid, vals, context=None):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param vals: dictionary of fields value.{‘name_of_the_field’: value, ...}
        @param context: A standard dictionary for contextual values
        @return: new record id for calendar_alarm.
        """
        if context is None:
            context = {}
        event_date = vals.get('event_date', False)
        if event_date:
            dtstart = datetime.strptime(vals['event_date'], "%Y-%m-%d %H:%M:%S")
            if vals['trigger_interval'] == 'days':
                delta = timedelta(days=vals['trigger_duration'])
            if vals['trigger_interval'] == 'hours':
                delta = timedelta(hours=vals['trigger_duration'])
            if vals['trigger_interval'] == 'minutes':
                delta = timedelta(minutes=vals['trigger_duration'])
            trigger_date = dtstart + (vals['trigger_occurs'] == 'after' and delta or -delta)
            vals['trigger_date'] = trigger_date
        res = super(calendar_alarm, self).create(cr, uid, vals, context=context)
        return res

    def do_run_scheduler(self, cr, uid, automatic=False, use_new_cursor=False, \
                       context=None):
        """Scheduler for event reminder
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of calendar alarm’s IDs.
        @param use_new_cursor: False or the dbname
        @param context: A standard dictionary for contextual values
        """
        return True # XXX FIXME REMOVE THIS AFTER FIXING get_recurrent_dates!!
        if context is None:
            context = {}
        current_datetime = datetime.now()
        request_obj = self.pool.get('res.request')
        alarm_ids = self.search(cr, uid, [('state', '!=', 'done')], context=context)

        mail_to = []

        for alarm in self.browse(cr, uid, alarm_ids, context=context):
            next_trigger_date = None
            update_vals = {}
            model_obj = self.pool.get(alarm.model_id.model)
            res_obj = model_obj.browse(cr, uid, alarm.res_id, context=context)
            re_dates = []

            if res_obj.rrule:
                event_date = datetime.strptime(res_obj.date, '%Y-%m-%d %H:%M:%S')
                recurrent_dates = get_recurrent_dates(res_obj.rrule, res_obj.exdate, event_date, res_obj.exrule)

                trigger_interval = alarm.trigger_interval
                if trigger_interval == 'days':
                    delta = timedelta(days=alarm.trigger_duration)
                if trigger_interval == 'hours':
                    delta = timedelta(hours=alarm.trigger_duration)
                if trigger_interval == 'minutes':
                    delta = timedelta(minutes=alarm.trigger_duration)
                delta = alarm.trigger_occurs == 'after' and delta or -delta

                for rdate in recurrent_dates:
                    if rdate + delta > current_datetime:
                        break
                    if rdate + delta <= current_datetime:
                        re_dates.append(rdate.strftime("%Y-%m-%d %H:%M:%S"))
                rest_dates = recurrent_dates[len(re_dates):]
                next_trigger_date = rest_dates and rest_dates[0] or None

            else:
                re_dates = [alarm.trigger_date]

            for r_date in re_dates:
                ref = alarm.model_id.model + ',' + str(alarm.res_id)

                # search for alreay sent requests
                if request_obj.search(cr, uid, [('trigger_date', '=', r_date), ('ref_doc1', '=', ref)], context=context):
                    continue

                if alarm.action == 'display':
                    value = {
                       'name': alarm.name,
                       'act_from': alarm.user_id.id,
                       'act_to': alarm.user_id.id,
                       'body': alarm.description,
                       'trigger_date': r_date,
                       'ref_doc1': ref
                    }
                    request_id = request_obj.create(cr, uid, value)
                    request_ids = [request_id]
                    for attendee in res_obj.attendee_ids:
                        if attendee.user_id:
                            value['act_to'] = attendee.user_id.id
                            request_id = request_obj.create(cr, uid, value)
                            request_ids.append(request_id)
                    request_obj.request_send(cr, uid, request_ids)

                if alarm.action == 'email':
                    sub = '[Openobject Reminder] %s' % (alarm.name)
                    body = """
Event: %s
Event Date: %s
Description: %s

From:
      %s

----
%s

"""  % (alarm.name, alarm.trigger_date, alarm.description, \
                        alarm.user_id.name, alarm.user_id.signature)
                    mail_to = [alarm.user_id.address_id.email]
                    for att in alarm.attendee_ids:
                        mail_to.append(att.user_id.address_id.email)
                    if mail_to:
                        tools.email_send(
                            tools.config.get('email_from', False),
                            mail_to,
                            sub,
                            body
                        )
            if next_trigger_date:
                update_vals.update({'trigger_date': next_trigger_date})
            else:
                update_vals.update({'state': 'done'})
            self.write(cr, uid, [alarm.id], update_vals)
        return True

calendar_alarm()


class calendar_event(osv.osv):
    _name = "calendar.event"
    _description = "Calendar Event"
    __attribute__ = {}

    def _tz_get(self, cr, uid, context=None):
        return [(x.lower(), x) for x in pytz.all_timezones]

    def onchange_allday(self, cr, uid, ids, allday, context=None):
        """Sets duration as 24 Hours if event is selected for all day
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of calendar event’s IDs.
        @param allday: Value of allday boolean
        @param context: A standard dictionary for contextual values
        """
        if not allday or not ids:
            return {}
        value = {
                 'duration': 24
                 }
        return {'value': value}

    def onchange_dates(self, cr, uid, ids, start_date, duration=False, end_date=False, allday=False, context=None):
        """Returns duration and/or end date based on values passed
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of calendar event’s IDs.
        @param start_date: Starting date
        @param duration: Duration between start date and end date
        @param end_date: Ending Datee
        @param context: A standard dictionary for contextual values
        """
        if context is None:
            context = {}

        value = {}
        if not start_date:
            return value
        if not end_date and not duration:
            duration = 1.00
            value['duration'] = duration

        if allday: # For all day event
            value = {'duration': 24}
            duration = 24.0

        start = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        if end_date and not duration:
            end = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
            diff = end - start
            duration = float(diff.days)* 24 + (float(diff.seconds) / 3600)
            value['duration'] = round(duration, 2)
        elif not end_date:
            end = start + timedelta(hours=duration)
            value['date_deadline'] = end.strftime("%Y-%m-%d %H:%M:%S")
        elif end_date and duration and not allday:
            # we have both, keep them synchronized:
            # set duration based on end_date (arbitrary decision: this avoid 
            # getting dates like 06:31:48 instead of 06:32:00)
            end = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
            diff = end - start
            duration = float(diff.days)* 24 + (float(diff.seconds) / 3600)
            value['duration'] = round(duration, 2)

        return {'value': value}

    def unlink_events(self, cr, uid, ids, context=None):
        """
        This function deletes event which are linked with the event with recurrent_uid
                (Removes the events which refers to the same UID value)
        """
        if context is None:
            context = {}
        for event_id in ids:
            cr.execute("select id from %s where recurrent_uid=%%s" % (self._table), (event_id,))
            r_ids = map(lambda x: x[0], cr.fetchall())
            self.unlink(cr, uid, r_ids, context=context)
        return True

    def _set_rrulestring(self, cr, uid, id, name, value, arg, context=None):
        """
        Sets values of fields that defines event recurrence from the value of rrule string
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param id: List of calendar event's ids.
        @param context: A standard dictionary for contextual values
        @return: dictionary of rrule value.
        """
        if context is None:
            context = {}
        cr.execute("UPDATE %s set freq='None',interval=0,count=0,end_date=Null,\
                    mo=False,tu=False,we=False,th=False,fr=False,sa=False,su=False,\
                    day=0,select1='date',month_list=Null ,byday=Null where id=%%s" % (self._table), (id,))

        if not value:
            cr.execute("UPDATE %s set rrule_type='none' where id=%%s" % self._table,(id,))
            return True
        val = {}
        for part in value.split(';'):
            if part.lower().__contains__('freq') and len(value.split(';')) <=2:
                rrule_type = part.lower()[5:]
                break
            else:
                rrule_type = 'custom'
                break
        ans = value.split(';')
        for i in ans:
            val[i.split('=')[0].lower()] = i.split('=')[1].lower()
        if not val.get('interval'):
            rrule_type = 'custom'
        elif int(val.get('interval')) > 1: #If interval is other than 1 rule is custom
            rrule_type = 'custom'

        qry = "UPDATE \"%s\" set rrule_type=%%s " % self._table
        qry_args = [ rrule_type, ]
        new_val = val.copy()
        for k, v in val.items():
            if  val['freq'] == 'weekly' and val.get('byday'):
                for day in val['byday'].split(','):
                    new_val[day] = True
                val.pop('byday')

            if val.get('until'):
                until = parser.parse(''.join((re.compile('\d')).findall(val.get('until'))))
                new_val['end_date'] = until.strftime('%Y-%m-%d')
                val.pop('until')
                new_val.pop('until')

            if val.get('bymonthday'):
                new_val['day'] = val.get('bymonthday')
                val.pop('bymonthday')
                new_val['select1'] = 'date'
                new_val.pop('bymonthday')

            if val.get('byday'):
                d = val.get('byday')
                if '-' in d:
                    new_val['byday'] = d[:2]
                    new_val['week_list'] = d[2:4].upper()
                else:
                    new_val['byday'] = d[:1]
                    new_val['week_list'] = d[1:3].upper()
                new_val['select1'] = 'day'

            if val.get('bymonth'):
                new_val['month_list'] = val.get('bymonth')
                val.pop('bymonth')
                new_val.pop('bymonth')

        for k, v in new_val.items():
            qry += ", %s=%%s" % k
            qry_args.append(v)

        qry = qry + " where id=%s"
        qry_args.append(id)
        cr.execute(qry, qry_args)
        return True

    def _get_rulestring(self, cr, uid, ids, name, arg, context=None):
        """
        Gets Recurrence rule string according to value type RECUR of iCalendar from the values given.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param id: List of calendar event's ids.
        @param context: A standard dictionary for contextual values
        @return: dictionary of rrule value.
        """
        result = {}
        for datas in self.read(cr, uid, ids, context=context):
            event = datas['id']
            if datas.get('rrule_type'):
                if datas.get('rrule_type') == 'none':
                    result[event] = False
                    cr.execute("UPDATE %s set exrule=Null where id=%%s" % self._table,( event,))
                if datas.get('rrule_type') :
                    if datas.get('interval', 0) < 0:
                        raise osv.except_osv(_('Warning!'), _('Interval can not be Negative'))
                    if datas.get('count', 0) < 0:
                        raise osv.except_osv(_('Warning!'), _('Count can not be Negative'))
                    rrule_custom = self.compute_rule_string(cr, uid, datas, \
                                                         context=context)
                    result[event] = rrule_custom
                else:
                    result[event] = self.compute_rule_string(cr, uid, {'freq': datas.get('rrule_type').upper(), 'interval': 1}, context=context)

        for id, myrule in result.items():
            #Remove the events generated from recurrent event
            if not myrule:
                self.unlink_events(cr, uid, [id], context=context)
        return result

    _columns = {
        'id': fields.integer('ID'),
        'sequence': fields.integer('Sequence'),
        'name': fields.char('Description', size=64, required=False, states={'done': [('readonly', True)]}),
        'date': fields.datetime('Date', states={'done': [('readonly', True)]}),
        'date_deadline': fields.datetime('Deadline', states={'done': [('readonly', True)]}),
        'create_date': fields.datetime('Created', readonly=True),
        'duration': fields.float('Duration', states={'done': [('readonly', True)]}),
        'description': fields.text('Description', states={'done': [('readonly', True)]}),
        'class': fields.selection([('public', 'Public'), ('private', 'Private'), \
             ('confidential', 'Confidential')], 'Mark as', states={'done': [('readonly', True)]}),
        'location': fields.char('Location', size=264, help="Location of Event", states={'done': [('readonly', True)]}),
        'show_as': fields.selection([('free', 'Free'), ('busy', 'Busy')], \
                                                'Show as', states={'done': [('readonly', True)]}),
        'base_calendar_url': fields.char('Caldav URL', size=264),
        'state': fields.selection([('tentative', 'Tentative'),
                        ('confirmed', 'Confirmed'),
                        ('cancelled', 'Cancelled')], 'State', readonly=True),
        'exdate': fields.text('Exception Date/Times', help="This property \
defines the list of date/time exceptions for a recurring calendar component."),
        'exrule': fields.char('Exception Rule', size=352, help="Defines a \
rule or repeating pattern of time to exclude from the recurring rule."),
        'rrule': fields.function(_get_rulestring, type='char', size=124, method=True, \
                                    string='Recurrent Rule', store=True, \
                                    fnct_inv=_set_rrulestring, help='Defines a\
 rule or repeating pattern for recurring events\n\
e.g.: Every other month on the last Sunday of the month for 10 occurrences:\
        FREQ=MONTHLY;INTERVAL=2;COUNT=10;BYDAY=-1SU'),
        'rrule_type': fields.selection([('none', ''), ('daily', 'Daily'), \
                            ('weekly', 'Weekly'), ('monthly', 'Monthly'), \
                            ('yearly', 'Yearly'),], 
                            'Recurrency', states={'done': [('readonly', True)]},
                            help="Let the event automatically repeat at that interval"),
        'alarm_id': fields.many2one('res.alarm', 'Alarm', states={'done': [('readonly', True)]},
                        help="Set an alarm at this time, before the event occurs" ),
        'base_calendar_alarm_id': fields.many2one('calendar.alarm', 'Alarm'),
        'recurrent_uid': fields.integer('Recurrent ID'),
        'recurrent_id': fields.datetime('Recurrent ID date'),
        'vtimezone': fields.selection(_tz_get, size=64, string='Timezone'),
        'user_id': fields.many2one('res.users', 'Responsible', states={'done': [('readonly', True)]}),
        'organizer': fields.char("Organizer", size=256, states={'done': [('readonly', True)]}), # Map with Organizer Attribure of VEvent.
        'organizer_id': fields.many2one('res.users', 'Organizer', states={'done': [('readonly', True)]}),
        'freq': fields.selection([('None', 'No Repeat'),
                                ('hourly', 'Hours'),
                                ('daily', 'Days'),
                                ('weekly', 'Weeks'),
                                ('monthly', 'Months'),
                                ('yearly', 'Years'), ], 'Frequency'),
          
        'end_type' : fields.selection([('forever', 'Forever'), ('count', 'Fix amout of times'), ('end_date','End date')], 'Way to end reccurency'),
        'interval': fields.integer('Repeat every', help="Repeat every (Days/Week/Month/Year)"),
        'count': fields.integer('Repeat', help="Repeat x times"),
        'mo': fields.boolean('Mon'),
        'tu': fields.boolean('Tue'),
        'we': fields.boolean('Wed'),
        'th': fields.boolean('Thu'),
        'fr': fields.boolean('Fri'),
        'sa': fields.boolean('Sat'),
        'su': fields.boolean('Sun'),
        'select1': fields.selection([('date', 'Date of month'), 
                                    ('day', 'Day of month')], 'Option'),
        'day': fields.integer('Date of month'),
        'week_list': fields.selection([('MO', 'Monday'), ('TU', 'Tuesday'), \
                                   ('WE', 'Wednesday'), ('TH', 'Thursday'), \
                                   ('FR', 'Friday'), ('SA', 'Saturday'), \
                                   ('SU', 'Sunday')], 'Weekday'),
        'byday': fields.selection([('1', 'First'), ('2', 'Second'), \
                                   ('3', 'Third'), ('4', 'Fourth'), \
                                   ('5', 'Fifth'), ('-1', 'Last')], 'By day'),
        'month_list': fields.selection(months.items(), 'Month'),
        'end_date': fields.date('Repeat Until'),
        'attendee_ids': fields.many2many('calendar.attendee', 'event_attendee_rel', \
                                 'event_id', 'attendee_id', 'Attendees'),
        'allday': fields.boolean('All Day', states={'done': [('readonly', True)]}),
        'active': fields.boolean('Active', help="If the active field is set to \
         true, it will allow you to hide the event alarm information without removing it."),
        'recurrency': fields.boolean('Recurrent', help="Recurrent Meeting"),                                    
        'edit_all': fields.boolean('Edit All', help="Edit all Occurrences  of recurrent Meeting."),        
    }
    def default_organizer(self, cr, uid, context=None):
        user_pool = self.pool.get('res.users')
        user = user_pool.browse(cr, uid, uid, context=context)
        res = user.name
        if user.user_email:
            res += " <%s>" %(user.user_email)
        return res

    _defaults = {
            'end_type' : 'forever',
            'state': 'tentative',
            'class': 'public',
            'show_as': 'busy',
            'freq': 'None',
            'select1': 'date',
            'interval': 1,
            'active': 1,
            'user_id': lambda self, cr, uid, ctx: uid,
            'organizer': default_organizer,
            'edit_all' : False,
    }

    def onchange_edit_all(self, cr, uid, ids, rrule_type,edit_all, context=None):
        if not context:
            context = {}
    
        value = {}
        if edit_all and rrule_type:
            for id in ids:
              base_calendar_id2real_id(id)
        return value              

    def modify_all(self, cr, uid, event_ids, defaults, context=None, *args):
        """
        Modifies the recurring event
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param event_ids: List of crm meeting’s IDs.
        @param context: A standard dictionary for contextual values
        @return: True
        """
        for event_id in event_ids:
            event_id = base_calendar_id2real_id(event_id)

            defaults.pop('id')
            defaults.update({'table': self._table})

            qry = "UPDATE %(table)s set name = '%(name)s', \
                            date = '%(date)s', date_deadline = '%(date_deadline)s'"
            if defaults.get('alarm_id'):
                qry += ", alarm_id = %(alarm_id)s"
            if defaults.get('location'):
                qry += ", location = '%(location)s'"
            qry += "WHERE id = %s" % (event_id)
            cr.execute(qry, defaults)

        return True

    def get_recurrent_ids(self, cr, uid, select, base_start_date, base_until_date, limit=100):
        """Gives virtual event ids for recurring events based on value of Recurrence Rule
        This method gives ids of dates that comes between start date and end date of calendar views
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param base_start_date: Get Start Date
        @param base_until_date: Get End Date
        @param limit: The Number of Results to Return """

        if not limit:
            limit = 100
        if isinstance(select, (str, int, long)):
            ids = [select]
        else:
            ids = select
        result = []
        recur_dict = []
        if ids and (base_start_date or base_until_date):
            cr.execute("select m.id, m.rrule, m.date, m.date_deadline, m.duration, \
                            m.exdate, m.exrule, m.recurrent_id, m.recurrent_uid from " + self._table + \
                            " m where m.id = ANY(%s)", (ids,) )

            count = 0
            for data in cr.dictfetchall():
                start_date = base_start_date and datetime.strptime(base_start_date[:10]+ ' 00:00:00' , "%Y-%m-%d %H:%M:%S") or False
                until_date = base_until_date and datetime.strptime(base_until_date[:10]+ ' 23:59:59', "%Y-%m-%d %H:%M:%S") or False
                if count > limit:
                    break
                event_date = datetime.strptime(data['date'], "%Y-%m-%d %H:%M:%S")
#                To check: If the start date is replace by event date .. the event date will be changed by that of calendar code
                start_date = event_date
                if not data['rrule']:
                    if start_date and (event_date < start_date):
                        continue
                    if until_date and (event_date > until_date):
                        continue
                    idval = real_id2base_calendar_id(data['id'], data['date'])
                    if not data['recurrent_id']:
                        result.append(idval)
                        count += 1
                    else:
                        ex_id = real_id2base_calendar_id(data['recurrent_uid'], data['recurrent_id'])
                        ls = base_calendar_id2real_id(ex_id, with_date=data and data.get('duration', 0) or 0)
                        if not isinstance(ls, (str, int, long)) and len(ls) >= 2:
                            if ls[1] == data['recurrent_id']:
                                result.append(idval)
                        recur_dict.append(ex_id)
                else:
                    exdate = data['exdate'] and data['exdate'].split(',') or []
                    rrule_str = data['rrule']
                    new_rrule_str = []
                    rrule_until_date = False
                    is_until = False
                    for rule in rrule_str.split(';'):
                        name, value = rule.split('=')
                        if name == "UNTIL":
                            is_until = True
                            value = parser.parse(value)
                            rrule_until_date = parser.parse(value.strftime("%Y-%m-%d"))
                            if until_date and until_date >= rrule_until_date:
                                until_date = rrule_until_date
                            if until_date:
                                value = until_date.strftime("%Y%m%d%H%M%S")
                        new_rule = '%s=%s' % (name, value)
                        new_rrule_str.append(new_rule)
                    if not is_until and until_date:
                        value = until_date.strftime("%Y%m%d%H%M%S")
                        name = "UNTIL"
                        new_rule = '%s=%s' % (name, value)
                        new_rrule_str.append(new_rule)
                    new_rrule_str = ';'.join(new_rrule_str)
                    rdates = get_recurrent_dates(str(new_rrule_str), exdate, start_date, data['exrule'])
                    for r_date in rdates:
                        if start_date and r_date < start_date:
                            continue
                        if until_date and r_date > until_date:
                            continue
                        idval = real_id2base_calendar_id(data['id'], r_date.strftime("%Y-%m-%d %H:%M:%S"))
                        result.append(idval)
                        count += 1
        if result:
            ids = list(set(result)-set(recur_dict))
        if isinstance(select, (str, int, long)):
            return ids and ids[0] or False
        return ids

    def compute_rule_string(self, cr, uid, datas, context=None, *args):
        """
        Compute rule string according to value type RECUR of iCalendar from the values given.
        @param self: the object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param datas: dictionary of freq and interval value.
        @param context: A standard dictionary for contextual values
        @return: String value of the format RECUR of iCalendar
        """

        weekdays = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']
        weekstring = ''
        monthstring = ''
        yearstring = ''
        freq=datas.get('rrule_type')
        if  freq == 'none':
            return ''
            
        interval_srting = datas.get('interval') and (';INTERVAL=' + str(datas.get('interval'))) or ''

        if freq == 'weekly':
            byday = map(lambda x: x.upper(), filter(lambda x: datas.get(x) and x in weekdays, datas))
            if byday:
                weekstring = ';BYDAY=' + ','.join(byday)

        elif freq == 'monthly':
            if datas.get('select1')=='date' and (datas.get('day') < 1 or datas.get('day') > 31):
                raise osv.except_osv(_('Error!'), ("Please select proper Day of month"))
            if datas.get('select1')=='day':
                monthstring = ';BYDAY=' + datas.get('byday') + datas.get('week_list')
            elif datas.get('select1')=='date':
                monthstring = ';BYMONTHDAY=' + str(datas.get('day'))

       
        if datas.get('end_date'):
            datas['end_date'] = ''.join((re.compile('\d')).findall(datas.get('end_date'))) + 'T235959Z'
        enddate = (datas.get('count') and (';COUNT=' + str(datas.get('count'))) or '') +\
                             ((datas.get('end_date') and (';UNTIL=' + datas.get('end_date'))) or '')

        rrule_string = 'FREQ=' + freq.upper() + weekstring + interval_srting \
                            + enddate + monthstring + yearstring

        return rrule_string

    def search(self, cr, uid, args, offset=0, limit=100, order=None,
            context=None, count=False):
        """
        Overrides orm search method.
        @param cr: the current row, from the database cursor,
        @param user: the current user’s ID for security checks,
        @param args: list of tuples of form [(‘name_of_the_field’, ‘operator’, value), ...].
        @param offset: The Number of Results to Pass
        @param limit: The Number of Results to Return
        @param context: A standard dictionary for contextual values
        @param count: If its True the method returns number of records instead of ids
        @return: List of id
        """
        args_without_date = []
        start_date = False
        until_date = False

        for arg in args:
            if arg[0] not in ('date', unicode('date'), 'date_deadline', unicode('date_deadline')):
                args_without_date.append(arg)
            else:
                if arg[1] in ('>', '>='):
                    if start_date:
                        continue
                    start_date = arg[2]
                elif arg[1] in ('<', '<='):
                    if until_date:
                        continue
                    until_date = arg[2]
        res = super(calendar_event, self).search(cr, uid, args_without_date, \
                                 offset, limit, order, context, count)

        res = self.get_recurrent_ids(cr, uid, res, start_date, until_date, limit)
        return res
    

    def get_edit_all(self, cr, uid, id, vals=None):
        """
            return true if we have to edit all meeting from the same recurrent
            or only on occurency
        """
        meeting = self.read(cr,uid, id, ['edit_all', 'recurrency'] )
        if(vals and 'edit_all' in vals): #we jsut check edit_all
            return vals['edit_all']
        else: #it's a recurrent event and edit_all is already check
            return meeting['recurrency'] and meeting['edit_all'] 


        

    def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
        """
        Overrides orm write method.
        @param self: the object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of crm meeting's ids
        @param vals: Dictionary of field value.
        @param context: A standard dictionary for contextual values
        @return: True
        """
        if context is None:
            context = {}
        if isinstance(ids, (str, int, long)):
            select = [ids]
        else:
            select = ids
        new_ids = []
        res = False
        for event_id in select:
            real_event_id = base_calendar_id2real_id(event_id)
            

            if(self.get_edit_all(cr, uid, event_id, vals=vals)):
                event_id = real_event_id
            
            
            if len(str(event_id).split('-')) > 1:
                data = self.read(cr, uid, event_id, ['date', 'date_deadline', \
                                                    'rrule', 'duration', 'exdate'])
                if data.get('rrule'):
                    data.update(vals)
                    data.update({
                        'recurrent_uid': real_event_id,
                        'recurrent_id': data.get('date'),
                        'rrule_type': 'none',
                        'rrule': '',
                        'edit_all': False,
                        'recurrency' : False,
                        })
                    
                    new_id = self.copy(cr, uid, real_event_id, default=data, context=context)
                    
                    date_new = event_id.split('-')[1]
                    date_new = time.strftime("%Y%m%dT%H%M%S", \
                                 time.strptime(date_new, "%Y%m%d%H%M%S"))
                    exdate = (data['exdate'] and (data['exdate'] + ',')  or '') + date_new
                    res = self.write(cr, uid, [real_event_id], {'exdate': exdate})
                    
                    context.update({'active_id': new_id, 'active_ids': [new_id]})
                    continue
            if not real_event_id in new_ids:
                new_ids.append(real_event_id)

        if vals.get('vtimezone', '') and vals.get('vtimezone', '').startswith('/freeassociation.sourceforge.net/tzfile/'):
            vals['vtimezone'] = vals['vtimezone'][40:]

        updated_vals = self.onchange_dates(cr, uid, new_ids,
            vals.get('date', False),
            vals.get('duration', False),
            vals.get('date_deadline', False),
            vals.get('allday', False),
            context=context)
        vals.update(updated_vals.get('value', {}))

        if not 'edit_all' in vals:
            vals['edit_all'] = False

        if new_ids:
            res = super(calendar_event, self).write(cr, uid, new_ids, vals, context=context)

        if ('alarm_id' in vals or 'base_calendar_alarm_id' in vals)\
                or ('date' in vals or 'duration' in vals or 'date_deadline' in vals):
            # change alarm details
            alarm_obj = self.pool.get('res.alarm')
            alarm_obj.do_alarm_create(cr, uid, new_ids, self._name, 'date', context=context)
        return res

    def browse(self, cr, uid, ids, context=None, list_class=None, fields_process=None):
        """
        Overrides orm browse method.
        @param self: the object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of crm meeting's ids
        @param context: A standard dictionary for contextual values
        @return: the object list.
        """
        if isinstance(ids, (str, int, long)):
            select = [ids]
        else:
            select = ids
        select = map(lambda x: base_calendar_id2real_id(x), select)
        res = super(calendar_event, self).browse(cr, uid, select, context, \
                                                    list_class, fields_process)
        if isinstance(ids, (str, int, long)):
            return res and res[0] or False

        return res

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        """
        Overrides orm Read method.Read List of fields for calendar event.
        @param cr: the current row, from the database cursor,
        @param user: the current user’s ID for security checks,
        @param ids: List of calendar event's id.
        @param fields: List of fields.
        @param context: A standard dictionary for contextual values
        @return: List of Dictionary of form [{‘name_of_the_field’: value, ...}, ...]
        """
        # FIXME This whole id mangling has to go!
        if context is None:
            context = {}

        if isinstance(ids, (str, int, long)):
            select = [ids]
        else:
            select = ids
        select = map(lambda x: (x, base_calendar_id2real_id(x)), select)
        result = []
        if fields and 'date' not in fields:
            fields.append('date')
        if fields and 'duration' not in fields:
            fields.append('duration')


        for base_calendar_id, real_id in select:
            #REVET: Revision ID: olt@tinyerp.com-20100924131709-cqsd1ut234ni6txn
            res = super(calendar_event, self).read(cr, uid, real_id, fields=fields, context=context, load=load)
            if not res :
                continue
            ls = base_calendar_id2real_id(base_calendar_id, with_date=res and res.get('duration', 0) or 0)
            if not isinstance(ls, (str, int, long)) and len(ls) >= 2:
                res['date'] = ls[1]
                res['date_deadline'] = ls[2]
            res['id'] = base_calendar_id

            result.append(res)
        if isinstance(ids, (str, int, long)):
            return result and result[0] or False
        return result

    def copy(self, cr, uid, id, default=None, context=None):
        """
        Duplicate record on specified id.
        @param self: the object pointer.
        @param cr: the current row, from the database cursor,
        @param id: id of record from which we duplicated.
        @param context: A standard dictionary for contextual values
        @return: Duplicate record id.
        """
        if context is None:
            context = {}
        res = super(calendar_event, self).copy(cr, uid, base_calendar_id2real_id(id), default, context)
        alarm_obj = self.pool.get('res.alarm')
        alarm_obj.do_alarm_create(cr, uid, [res], self._name, 'date', context=context)

        return res

    def unlink(self, cr, uid, ids, context=None):
        """
        Deletes records specified in ids.
        @param self: the object pointer.
        @param cr: the current row, from the database cursor,
        @param id: List of calendar event's id.
        @param context: A standard dictionary for contextual values
        @return: True
        """
        res = False
        for event_datas in self.read(cr, uid, ids, ['date', 'rrule', 'exdate'], context=context):
            event_id = event_datas['id']
            
            if self.get_edit_all(cr, uid, event_id, vals=None):
                event_id = base_calendar_id2real_id(event_id)
            
            if isinstance(event_id, (int, long)):
                res = super(calendar_event, self).unlink(cr, uid, event_id, context=context)
                self.pool.get('res.alarm').do_alarm_unlink(cr, uid, [event_id], self._name)
                self.unlink_events(cr, uid, [event_id], context=context)
            else:
                str_event, date_new = event_id.split('-')
                event_id = int(str_event)
                if event_datas['rrule']:
                    # Remove one of the recurrent event
                    date_new = time.strftime("%Y%m%dT%H%M%S", \
                                 time.strptime(date_new, "%Y%m%d%H%M%S"))
                    exdate = (event_datas['exdate'] and (event_datas['exdate'] + ',')  or '') + date_new
                    res = self.write(cr, uid, [event_id], {'exdate': exdate})
                else:
                    res = super(calendar_event, self).unlink(cr, uid, [event_id], context=context)
                    self.pool.get('res.alarm').do_alarm_unlink(cr, uid, [event_id], self._name)
                    self.unlink_events(cr, uid, [event_id], context=context)
        return res

    def create(self, cr, uid, vals, context=None):
        """
        Create new record.
        @param self: the object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param vals: dictionary of every field value.
        @param context: A standard dictionary for contextual values
        @return: new created record id.
        """
        if context is None:
            context = {}

        if vals.get('vtimezone', '') and vals.get('vtimezone', '').startswith('/freeassociation.sourceforge.net/tzfile/'):
            vals['vtimezone'] = vals['vtimezone'][40:]

        updated_vals = self.onchange_dates(cr, uid, [],
            vals.get('date', False),
            vals.get('duration', False),
            vals.get('date_deadline', False),
            vals.get('allday', False),
            context=context)
        vals.update(updated_vals.get('value', {}))

        res = super(calendar_event, self).create(cr, uid, vals, context)
        alarm_obj = self.pool.get('res.alarm')
        alarm_obj.do_alarm_create(cr, uid, [res], self._name, 'date', context=context)
        return res

    def do_tentative(self, cr, uid, ids, context=None, *args):
        """ Makes event invitation as Tentative
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of Event IDs
        @param *args: Get Tupple value
        @param context: A standard dictionary for contextual values
        """
        return self.write(cr, uid, ids, {'state': 'tentative'}, context)

    def do_cancel(self, cr, uid, ids, context=None, *args):
        """ Makes event invitation as Tentative
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of Event IDs
        @param *args: Get Tupple value
        @param context: A standard dictionary for contextual values
        """
        return self.write(cr, uid, ids, {'state': 'cancelled'}, context)

    def do_confirm(self, cr, uid, ids, context=None, *args):
        """ Makes event invitation as Tentative
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of Event IDs
        @param *args: Get Tupple value
        @param context: A standard dictionary for contextual values
        """
        return self.write(cr, uid, ids, {'state': 'confirmed'}, context)

calendar_event()

class calendar_todo(osv.osv):
    """ Calendar Task """

    _name = "calendar.todo"
    _inherit = "calendar.event"
    _description = "Calendar Task"

    def _get_date(self, cr, uid, ids, name, arg, context=None):
        """
        Get Date
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of calendar todo's IDs.
        @param args: list of tuples of form [(‘name_of_the_field’, ‘operator’, value), ...].
        @param context: A standard dictionary for contextual values
        """

        res = {}
        for event in self.browse(cr, uid, ids, context=context):
            res[event.id] = event.date_start
        return res

    def _set_date(self, cr, uid, id, name, value, arg, context=None):
        """
        Set Date
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param id: calendar's ID.
        @param value: Get Value
        @param args: list of tuples of form [(‘name_of_the_field’, ‘operator’, value), ...].
        @param context: A standard dictionary for contextual values
        """
        
        assert name == 'date'
        return self.write(cr, uid, id, { 'date_start': value }, context=context)

    _columns = {
        'date': fields.function(_get_date, method=True, fnct_inv=_set_date, \
                            string='Duration', store=True, type='datetime'),
        'duration': fields.integer('Duration'),
    }

    __attribute__ = {}


calendar_todo()

class ir_attachment(osv.osv):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    def search_count(self, cr, user, args, context=None):
        """
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param user: the current user’s ID for security checks,
        @param args: list of tuples of form [(‘name_of_the_field’, ‘operator’, value), ...].
        @param context: A standard dictionary for contextual values
        """

        args1 = []
        for arg in args:
            args1.append(map(lambda x:str(x).split('-')[0], arg))
        return super(ir_attachment, self).search_count(cr, user, args1, context)
        
        
    
    def create(self, cr, uid, vals, context=None):
        if context:
            id = context.get('default_res_id', False)
            context.update({'default_res_id' : base_calendar_id2real_id(id)})
        return super(ir_attachment, self).create(cr, uid, vals, context=context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        """
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param args: list of tuples of form [(‘name_of_the_field’, ‘operator’, value), ...].
        @param offset: The Number of Results to pass,
        @param limit: The Number of Results to Return,
        @param context: A standard dictionary for contextual values
        """

        new_args = args
        for i, arg in enumerate(new_args):
            if arg[0] == 'res_id':
                new_args[i] = (arg[0], arg[1], base_calendar_id2real_id(arg[2]))

        return super(ir_attachment, self).search(cr, uid, new_args, offset=offset,
                            limit=limit, order=order, context=context, count=False)
ir_attachment()

class ir_values(osv.osv):
    _inherit = 'ir.values'

    def set(self, cr, uid, key, key2, name, models, value, replace=True, \
            isobject=False, meta=False, preserve_user=False, company=False):
        """
        Set IR Values
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param model: Get The Model
        """

        new_model = []
        for data in models:
            if type(data) in (list, tuple):
                new_model.append((data[0], base_calendar_id2real_id(data[1])))
            else:
                new_model.append(data)
        return super(ir_values, self).set(cr, uid, key, key2, name, new_model, \
                    value, replace, isobject, meta, preserve_user, company)

    def get(self, cr, uid, key, key2, models, meta=False, context=None, \
             res_id_req=False, without_user=True, key2_req=True):
        """
        Get IR Values
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param model: Get The Model
        """
        if context is None:
            context = {}
        new_model = []
        for data in models:
            if type(data) in (list, tuple):
                new_model.append((data[0], base_calendar_id2real_id(data[1])))
            else:
                new_model.append(data)
        return super(ir_values, self).get(cr, uid, key, key2, new_model, \
                         meta, context, res_id_req, without_user, key2_req)

ir_values()

class ir_model(osv.osv):

    _inherit = 'ir.model'

    def read(self, cr, uid, ids, fields=None, context=None,
            load='_classic_read'):
        """
        Overrides orm read method.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of IR Model’s IDs.
        @param context: A standard dictionary for contextual values
        """
        new_ids = isinstance(ids, (str, int, long)) and [ids] or ids
        if context is None:
            context = {}
        data = super(ir_model, self).read(cr, uid, new_ids, fields=fields, \
                        context=context, load=load)
        if data:
            for val in data:
                val['id'] = base_calendar_id2real_id(val['id'])
        return isinstance(ids, (str, int, long)) and data[0] or data

ir_model()

class virtual_report_spool(web_services.report_spool):

    def exp_report(self, db, uid, object, ids, datas=None, context=None):
        """
        Export Report
        @param self: The object pointer
        @param db: get the current database,
        @param uid: the current user’s ID for security checks,
        @param context: A standard dictionary for contextual values
        """

        if object == 'printscreen.list':
            return super(virtual_report_spool, self).exp_report(db, uid, \
                            object, ids, datas, context)
        new_ids = []
        for id in ids:
            new_ids.append(base_calendar_id2real_id(id))
        if datas.get('id', False):
            datas['id'] = base_calendar_id2real_id(datas['id'])
        return super(virtual_report_spool, self).exp_report(db, uid, object, new_ids, datas, context)

virtual_report_spool()

class res_users(osv.osv):
    _inherit = 'res.users'

    def _get_user_avail(self, cr, uid, ids, context=None):
        """
        Get User Availability
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of res user’s IDs.
        @param context: A standard dictionary for contextual values
        """

        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        res = {}
        attendee_obj = self.pool.get('calendar.attendee')
        attendee_ids = attendee_obj.search(cr, uid, [
                    ('event_date', '<=', current_datetime), ('event_end_date', '<=', current_datetime),
                    ('state', '=', 'accepted'), ('user_id', 'in', ids)
                    ])

        for attendee_data in attendee_obj.read(cr, uid, attendee_ids, ['user_id']):
            user_id = attendee_data['user_id']
            status = 'busy'
            res.update({user_id:status})

        #TOCHECK: Delegated Event
        for user_id in ids:
            if user_id not in res:
                res[user_id] = 'free'

        return res

    def _get_user_avail_fun(self, cr, uid, ids, name, args, context=None):
        """
        Get User Availability Function
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of res user’s IDs.
        @param context: A standard dictionary for contextual values
        """

        return self._get_user_avail(cr, uid, ids, context=context)

    _columns = {
            'availability': fields.function(_get_user_avail_fun, type='selection', \
                    selection=[('free', 'Free'), ('busy', 'Busy')], \
                    string='Free/Busy', method=True),
    }

res_users()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
