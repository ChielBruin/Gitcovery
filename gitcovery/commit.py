import re, datetime

from .diff import Diff

class Commit:
	_author = None
	_authorDate = ''
	_commit = None
	_commitDate = ''
	_title = ''
	_msg = ''
	_diff = None
	
	def __init__(self, sha: str) -> None:
		self.sha = sha.replace('"', '')
		
	def load(self) -> None:
		if self._author:
			return
		
		from .git import Git
		out = Git.call(['show', '--pretty=fuller', self.sha])
		matcher = re.search('Author:\s*(?P<author>.+)\s*<(?P<authorMail>.+@.+)>\nAuthorDate: (?P<authorDate>.*)\n'+ 
							'Commit: (?P<commit> .*) <(?P<commitMail>.*@.*)>\nCommitDate:\s*(?P<commitDate>.+)\n\n' + 
							'\s*(?P<title>.+)((\n\s*)*(?P<message>(.*\n)*))?(?P<diff>diff (.*\n)*)', out)
					
		if not matcher:
			raise Exception('git show output could not be matched: ' + out + '\n\nIf you are sure this should be matched, please report the output so I can improve the regex')
			  
		self._author = Git.getAuthor(matcher.group('author'), email=matcher.group('authorMail'))
		self._commit = Git.getAuthor(matcher.group('commit'), email=matcher.group('commitMail'))
		
		self._author.registerCommit(self)
		
		# This might break when the git and system languages are not the same.
		self._authorDate = datetime.datetime.strptime(matcher.group('authorDate'), '%a %b %d %H:%M:%S %Y %z').date()
		self._commitDate = datetime.datetime.strptime(matcher.group('commitDate'), '%a %b %d %H:%M:%S %Y %z').date()
		
		self._title      = matcher.group('title')
		self._msg        = matcher.group('message') if matcher.group('message') else ''
		self._diff = Diff.fromString(matcher.group('diff'))
		
	def author(self) -> 'Author':
		if not self._author:
			self.load()
		return self._author

	def authorDate(self) -> datetime.date:
		if not self._authorDate:
			self.load()
		return self._authorDate
		
	def commit(self) -> 'Author':
		if not self._commit:
			self.load()
		return self._commit
		
	def commitDate(self) -> datetime.date:
		if not self._commitDate:
			self.load()
		return self._commitDate

	def title(self) -> str:
		if not self._title:
			self.load()
		return self._title

	def msg(self) -> str:
		if not self._msg:
			self.load()
		return self._msg

	def changes(self, fileName=None) -> Diff:
		if not self._diff:
			self.load()
		
		if fileName:
			return self._diff.getFile(fileName)
		else:
			return self._diff
