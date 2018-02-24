import re

class FileDiff(object):
	def __init__(self, fname, nums, diff):
		self.name = fname
		self.nums = nums
		self.diff = diff
		#print(fname, nums, diff)
		
	def __len__(self):
		#TODO
		return len(diff)

class Diff(object):
	def __init__(self):
		self.data = {}
		
	def add(self, fileDiff):
		if fileDiff.name in self.data:
			raise Exception('Diff already present for ' + fname)
		self.data[fileDiff.name] = fileDiff
	
	@staticmethod
	def fromString(data):	
		matchIter = re.finditer('diff --git a/(?P<fname>.*) b/(?P=fname)(\nnew file mode .*)*\nindex.*\n--- (a/(?P=fname)|/dev/null)\n\+\+\+ b/(?P=fname)\n'+
								'@@ (?P<nums>-[0-9]+,[0-9]+ \+[0-9]+,[0-9]+) @@\s(?P<diff>.*\n([\s+-].*\n*)*)', data)
		obj = Diff()
		for matcher in matchIter:
			diff = FileDiff(matcher.group('fname'),
				matcher.group('nums'),
				matcher.group('diff'))
			obj.add(diff)
		return obj
		
	def getFile(self, fname: str) -> 'Diff':
		return self.data[fname]

	def __len__(self):
		return len(self.data)
