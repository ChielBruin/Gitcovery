import re

class _Diffable(object):
	def __init__(self, diffs):
		self._diffs = diffs

	def __len__(self):
		'''
		Get the number of changed lines in this Diff
		'''
		total = 0
		for d in self._diffs:
			total += len(d)
		return total
	
	def numAdded(self):
		'''
		Get the number of added lines in this Diff
		'''
		total = 0
		for d in self._diffs:
			total += d.numAdded()
		return total
	
	def numRemoved(self):
		'''
		Get the number of removed lines in this Diff
		'''
		total = 0
		for d in self._diffs:
			total += d.numRemoved()
		return total

class BlobDiff(_Diffable):
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
		#TODO: This counts duplicates
		return len(self.added) + len(self.removed)

	def numAdded(self):
		return len(self.added)

	def numRemoved(self):
		return len(self.removed)

class FileDiff(_Diffable):
	def __init__(self, fname, diff):
		super(FileDiff, self).__init__([])
		self.name = fname
		matchIter = re.finditer('@@ (?P<nums>-[0-9]+,[0-9]+ \+[0-9]+,[0-9]+) @@\s(?P<diff>.*\n([\s+-].*\n*)*)', diff)
		for match in matchIter:
			self._diffs.append(BlobDiff(match.group('nums'), match.group('diff')))

class Diff(_Diffable):
	def __init__(self):
		super(Diff, self).__init__([])
		self.data = {}
		
	def add(self, fileDiff):
		if fileDiff.name in self.data:
			raise Exception('Diff already present for ' + fname)
		self.data[fileDiff.name] = fileDiff
		self._diffs.append(fileDiff)
	
	@staticmethod
	def fromString(data):
		if not data:
			return Diff()
		matchIter = re.finditer('diff --git a/(?P<fname>.*) b/(?P=fname)(\nnew file mode .*)*\nindex.*\n'+ 
								'--- (a/(?P=fname)|/dev/null)\n\+\+\+ b/(?P=fname)\n(?P<diff>@@ (.*\n)*)', data)
		obj = Diff()
		for matcher in matchIter:
			diff = FileDiff(matcher.group('fname'), matcher.group('diff'))
			obj.add(diff)
		return obj
		
	def getFile(self, fname: str) -> 'Diff':
		return self.data[fname]
