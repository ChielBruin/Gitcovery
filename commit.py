import gitfs
from diff import Diff


class Commit:
	_author = ''
	_authorDate = ''
	_commit = ''
	_commitDate = ''
	_title = ''
	_msg = ''
	_diff = None
	
	def __init__(self, sha: str) -> None:
		self.sha = sha
		
	def getData(self) -> None:
		if self._author:
			return
		out = gitfs.Git.call(['log', '-n', '1', self.sha, '--pretty=fuller'])
		#TODO
		#print(out)
		self.data = True
	
	def getDiff(self) -> None:
		if self._diff:
			return
		out = gitfs.Git.call(['diff', self.sha + '^', self.sha])
		#TODO
		#print(out)
		self._diff = Diff(out)
		
	@property
	def author(self) -> str:
		if not self.data:
			self.getData()
		return self._author
			
	def changes(self, fileName=None) -> Diff:
		if not self._diff:
			self.getDiff()
		
		if fileName:
			return self._diff.getFile(fileName)
		else:
			return self._diff
