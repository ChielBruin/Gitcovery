import re

class FileDiff(object):
	def __init__(self, fname, diff):
		self.name = fname
		self.raw = []
		matchIter = re.finditer('@@ (?P<nums>-[0-9]+,[0-9]+ \+[0-9]+,[0-9]+) @@\s(?P<diff>.*\n([\s+-].*\n*)*)', diff)
		for match in matchIter:
			self.raw.append((match.group('nums'), match.group('diff')))
		#print(fname, self.raw)
		
	def __len__(self):
		#TODO
		return len(self.raw)

class Diff(object):
	def __init__(self):
		self.data = {}
		
	def add(self, fileDiff):
		if fileDiff.name in self.data:
			raise Exception('Diff already present for ' + fname)
		self.data[fileDiff.name] = fileDiff
	
	@staticmethod
	def fromString(data):	
		matchIter = re.finditer('diff --git a/(?P<fname>.*) b/(?P=fname)(\nnew file mode .*)*\nindex.*\n'+ 
								'--- (a/(?P=fname)|/dev/null)\n\+\+\+ b/(?P=fname)\n(?P<diff>@@ (.*\n)*)', data)
		obj = Diff()
		for matcher in matchIter:
			diff = FileDiff(matcher.group('fname'), matcher.group('diff'))
			obj.add(diff)
		return obj
		
	def getFile(self, fname: str) -> 'Diff':
		return self.data[fname]

	def __len__(self):
		return len(self.data)
