import re, datetime

import gitfs
from diff import Diff


class Commit:
	_author = ''
	_authorMail = ''
	_commitDate = ''
	_title = ''
	_msg = ''
	_diff = None
	
	def __init__(self, sha: str) -> None:
		self.sha = sha.replace('"', '')
		
	def getData(self) -> None:
		if self._author:
			return
		out = gitfs.Git.call(['show', '--pretty=fuller', self.sha])
		matcher = re.search('Author:\s*(?P<author>.+)\s*<(?P<authorMail>.+@.+)>\n.*\n.*\nCommitDate:\s*(?P<commitDate>.+)\n\n' +
							'\s*(?P<title>.+)((\n\s*)*(?P<message>(.*\n)*))?(?P<diff>diff (.*\n)*)', out)
					
		if not matcher:
			raise Exception('git show output could not be matched: ' + out + '\n\nIf you are sure this should be matched, please report the output so I can improve the regex')
			  
		self._author     = matcher.group('author')
		self._authorMail = matcher.group('authorMail')
		dateString       = matcher.group('commitDate')
		
		# This might break when the git and system languages are not the same.
		self._commitDate = datetime.datetime.strptime(dateString, '%a %b %d %H:%M:%S %Y %z').date()
		self._title      = matcher.group('title')
		self._msg        = matcher.group('message') if matcher.group('message') else ''
		
		self._diff = Diff.fromString(matcher.group('diff'))
		
		self.data = True
		
	def author(self) -> str:
		if not self._author:
			self.getData()
		return self._author

	def authorMail(self) -> str:
		if not self._authorMail:
			self.getData()
		return self._authorMail

	def commitDate(self) -> datetime.date:
		if not self._commitDate:
			self.getData()
		return self._commitDate

	def title(self) -> str:
		if not self._title:
			self.getData()
		return self._title

	def msg(self) -> str:
		if not self._msg:
			self.getData()
		return self._msg

	def changes(self, fileName=None) -> Diff:
		if not self._diff:
			self.getData()
		
		if fileName:
			return self._diff.getFile(fileName)
		else:
			return self._diff
