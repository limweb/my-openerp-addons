
import mdx_input
import sqlalchemy
import common
import slicer
import datetime
import pooler

import copy

class mapper(object):
	def __init__(self, size):
		self.size = size

class query(object):
	def __init__(self, axis, cube, slicer_obj=None, *args):
		super(query, self).__init__()
		self.object = False
		self.cube = cube
		self.axis = axis
		if not slicer_obj:
			slicer_obj = slicer.slicer([])
		self.slicer = slicer_obj

	#
	# Generate the cube with 'False' values
	# This function could be improved
	#
	def _cube_create(self, cube_size):
		cube_data = [False]
		while cube_size:
			newcube = []
			for i in range(cube_size.pop()):
				newcube.append(copy.deepcopy(cube_data))
			cube_data = newcube
		return cube_data

	def run(self):
		db = sqlalchemy.create_engine(self.object.schema_id.database_id.connection_url,encoding='utf-8')
		metadata = sqlalchemy.MetaData(db)
		print 'Connected to database...', self.object.schema_id.database_id.connection_url

		#
		# Compute axis
		#

		axis = []
		axis_result = []
		cube_size = []

		for ax in self.axis:
			result = ax.run(metadata)
			length = 0
			axis_result2 = []
			for r in result:
				length += len(r['value'])
				axis_result2 += map(lambda x: (map(lambda y: y or False,x[0]),x[1] or False), r['value'])
			axis_result.append(axis_result2)
			axis.append(result)
			cube_size.append(length)

		cube_data = self._cube_create(cube_size)

		slice = self.slicer.run(metadata)
		position = 0
		for subset in common.xcombine(*axis):
			select,table_fact = self.cube.run(metadata)
			for s in subset+slice:
				for key,val in s['query'].items():
					for v in val:
						if key=='column':
							v = v.label('p_%d' % (position,))
							position += 1
							select.append_column(v)
						elif key=='whereclause':
#							print 'ADding',v
							select.append_whereclause(v)
						elif key=='group_by':
							select.append_group_by(v)
						else:
							raise 'Error, %s not implemented !'% (key,)
			metadata.bind.echo = True
			
			query = select.execute()
			result = query.fetchall()
			for record in result:
				cube = cube_data
				r = list(record)
				value = False
				for s in subset:
					cube = s['axis_mapping'].cube_set(cube, r, s['delta'])
					value = s['axis_mapping'].value_set(r) or value
				for s in slice:
					value = s['axis_mapping'].value_set(r) or value

				if value:
					assert not cube[0], 'Already a value in cube, this is a bug !'
					cube[0] = value

		i=0
		for a in cube_data:
			i=i+1;
		return (axis_result, cube_data)

	def preprocess(self):
		wrapper = mdx_input.mdx_input()
		wrapper.parse(self)

	def validate(self, schema):
		""" This function takes a query object and validate and assign
		fact data to it. Browse object from Tiny ERP"""
		cube = self.cube.validate(schema)
		self.object = cube
		if not self.object:
			raise "Cube '%s' not found in the schema '%s' !"%(cube.name, schema.name)
		self.slicer.validate(cube)

		for axis in self.axis:
			axis.validate(cube)
		for dimension in cube.dimension_ids:
			pass
		return True,cube

	def __repr__(self):
		res = '<olap.query ['+str(self.cube)+']\n'
		for l in self.axis:
			res+= '\tAxis: '+str(l)+'\n'
		res+= '\tSlicer:\n'+str(self.slicer)+'\n'
		res += '>'
		return res

	def log(self,cr,uid,cube,query,context={}):
		if not context==False:
			print "Logging Query..."
			logentry={}
			logentry['user_id']=uid
			logentry['cube_id']=cube.id
			logentry['query']=query
			logentry['time']= str(datetime.datetime.now())
			logentry['result_size']=0
	
			log_id = pooler.get_pool(cr.dbname).get('olap.query.logs').create(cr,uid,logentry)
			return log_id
		return -1
# vim: ts=4 sts=4 sw=4 si et
