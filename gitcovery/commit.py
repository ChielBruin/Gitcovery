import re
from dateutil import parser as dateParser

from .git import Git
from .diff import Diff


class Commit(object):
	_REGEX_COMMIT = re.compile('(?P<parents>([a-f0-9\s]+\s?)*)\n'+ 
							   '(?P<author>.+)\n(?P<authorMail>.+@.+)\n(?P<authorDate>[0-9\-]+ [0-9:]+ [+\-0-9]+)\n' +
							   '(?P<commit>.+)\n(?P<commitMail>.+@.+)\n(?P<commitDate>[0-9\-]+ [0-9:]+ [+\-0-9]+)\n' +
							   '(?P<title>.*)(?P<message>(.*\n)*)?\n(?P<diff>diff (.*\n)*)?')

	def __init__(self, sha, preload=False):
		self.sha = sha.replace('"', '')
		self._author = None
		self._authorDate = ''
		self._commit = None
		self._commitDate = ''
		self._title = ''
		self._msg = ''
		self._diff = None
		self._parents = []
		self._children = []
		
		
		if preload:
			self.load()
		
	def load(self):
		if self._author:
			return
		
		out = Git.call(['show', '--pretty=format:%P%n%an%n%ae%n%ai%n%cn%n%ce%n%ci%n%s%n%b', self.sha])
		matcher = self._REGEX_COMMIT.search(out)
					
		if not matcher:
			raise Exception('git show output could not be matched: ' + out + '\n\nIf you are sure this should be matched, please report the output so I can improve the regex')
		
		for sha in matcher.group('parents').split(' '):
			if sha == '':
				continue
			commit = Git.getCommit(sha)
			self._parents.append(commit)
			commit.registerChild(self)
		
		self._author = Git.getAuthor(matcher.group('author'), email=matcher.group('authorMail'))
		self._commit = Git.getAuthor(matcher.group('commit'), email=matcher.group('commitMail'))
		
		self._author.registerCommit(self)
		
		self._authorDate = dateParser.parse(matcher.group('authorDate'))
		self._commitDate = dateParser.parse(matcher.group('commitDate'))

		self._title      = matcher.group('title')
		self._msg        = matcher.group('message') if matcher.group('message') else ''
		self._diff = Diff.fromString(matcher.group('diff'))

	def author(self):
		self.load()
		return self._author

	def authorDate(self):
		self.load()
		return self._authorDate
		
	def commit(self):
		self.load()
		return self._commit
		
	def commitDate(self):
		self.load()
		return self._commitDate

	def title(self):
		self.load()
		return self._title

	def msg(self):
		self.load()
		return self._msg

	def changes(self, fileName=None):
		self.load()
		if fileName:
			return self._diff.getFile(fileName)
		else:
			return self._diff

	def registerChild(self, commit):
		if not commit in self._children:
			self._children.append(commit)

	def parents(self):
		self.load()
		return self._parents

	def children(self):
		'''
		Get all the commits that registered themselves as children.
		This means that this list might not be complete, so please make sure all possible children are loaded.
		'''
		self.load()
		return self._children

	def __lt__(self, other):
		self.load()
		
		return self.authorDate() < other.authorDate()
		
	def forEachParent(self, func):
		'''
		Execute a function for this commit and all its parents (AKA the tree that this commit is part of).
		'''
		func(self)
		
		for child in self.parents():
			child.forEachChild(func)
