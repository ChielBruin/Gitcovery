class Diff(object):
	def __init__(self, data):
		self.data = data
		
	def getFile(self, fname: str) -> 'Diff':
		return self
