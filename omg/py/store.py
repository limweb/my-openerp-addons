from cgi import escape
from urllib import unquote
import xmlrpclib
import string

def index(req):
	s = """\
<html><head>
<style type="text/css">
td {padding:0.2em 0.5em;border:1px solid black;}
table {border-collapse:collapse;}
</style>
</head><body>
<form method="get" action="./store">
	<select name="chain"> %s </select>
	<input type="submit" value="Find" name="find"/>
	<br/>
	<table>
		%s
	</table>
	<input type="submit" value="Select" name="select"/>
	<input type="hidden" name="id" value="%s" />
	<input type="hidden" name="dbname" value="%s" />
</form>
</body></html>
"""
	parseduri = req.subprocess_env['QUERY_STRING']
	pairlist = string.split(parseduri, '&')
    	for pair in pairlist:
        	k,v = string.split(pair, '=')
        	if k == 'dbname':
              		db = v

	rid = ''
	record_id = req.form.getfirst('id','')
	if record_id:
		rid = record_id
	chain = req.form.getlist('chain')
	chain_id = ''
	if chain:
		chain_id = chain[0]

	store = req.form.getlist('store')
	store_ids = ''
	if store:
		select = req.form.getfirst('select','')
		if select:
			store_ids = store

	username = 'admin'
	pwd = 'admin'
	dbname = db

	attribs = ''
	sock_common = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/common')
	uid = sock_common.login(dbname, username, pwd)
	sock = xmlrpclib.ServerProxy('http://localhost:8069/xmlrpc/object')
	args = [('id', '!=', '-1')] #query clause
	ids = sock.execute(dbname, uid, pwd, 'omg.sale.chain', 'search', args)
	fields = ['id','name']
	results = sock.execute(dbname, uid, pwd, 'omg.sale.chain', 'read', ids, fields)

	for attrib in results:
		if chain:
			if str(attrib['id']) == chain_id:
				attribs += '<option value=%s selected="selected">%s</option>'
			else:
				attribs += '<option value=%s>%s</option>'
		else:
			attribs += '<option value=%s>%s</option>'
		attribs %= (str(attrib['id']),attrib['name'])

	attrib2s = ''
	if chain:
		args = [('chain_id', '=', int(chain_id))] 
		ids = sock.execute(dbname, uid, pwd, 'stock.location', 'search', args)
		fields = ['id','name']
		results = sock.execute(dbname, uid, pwd, 'stock.location', 'read', ids, fields)
		cols = 0
		attrib2s += "<tr>"
		for attrib in results:
			if cols == 4:
				attrib2s += "</tr><tr>"			
				attrib2s += '<td><input type="checkbox" name="store" value=%s>%s</input></td>'
				attrib2s %= (str(attrib['id']),attrib['name'])
				cols = 0
			else:
				attrib2s += '<td><input type="checkbox" name="store" value=%s>%s</input></td>'
				attrib2s %= (str(attrib['id']),attrib['name'])
			cols += 1
		attrib2s += "</tr>"
	if store:
		for i in range(len(store)):
			args = [('id', '=', int(store[i]))] 
			ids = sock.execute(dbname, uid, pwd, 'stock.location', 'search', args)
			fields = ['id','name']
			results = sock.execute(dbname, uid, pwd, 'stock.location', 'read', ids, fields)	
			for location in results:
				store_name = location['name']
				store_line = {
					'location_id': str(location['id']),
					'location_set_id': str(rid),
					'name': location['name']
				}
				sock.execute(dbname, uid, pwd, 'stock.location.set.line', 'create', store_line)
	if store:
		html = s % (attribs, attrib2s, rid, db)
	else:
		html = s % (attribs, attrib2s, rid, db)		

	return html

