import re

class BlobDiff(object):
	'''
	Class representing a code blob in the diff of a file.
	'''
	def __init__(self, nums, lines):
		#TODO: Store the actual diff data somehow
		self.added = []
		self.removed = []
		
		for line in lines.split('\n'):
			if line.startswith('+'):
				self.added.append(line)
			if line.startswith('-'):
				self.removed.append(line)

	def __len__(self):
		return len(self.added) + len(self.removed)

class FileDiff(object):
	def __init__(self, fname, diff):
		self.name = fname
		self.blobs = []
		matchIter = re.finditer('@@ (?P<nums>-[0-9]+,[0-9]+ \+[0-9]+,[0-9]+) @@\s(?P<diff>.*\n([\s+-].*\n*)*)', diff)
		for match in matchIter:
			self.blobs.append(BlobDiff(match.group('nums'), match.group('diff')))
		
	def __len__(self):
		total = 0
		for blob in self.blobs:
			total += len(blob)
		return total

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
		total = 0
		for fname in self.data:
			total += len(self.data[fname])
		return total
