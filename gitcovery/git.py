import subprocess, re, os
from typing import Dict, List

from .commit import Commit
from .author import Author

class Git(object):
	_commits = {}
	_authors = {}
	_tags = None
	root = ''
	
	@classmethod
	def _verifyRoot(cls):
		if not cls.root:
			raise Exception('Please set the git root first')

	@classmethod
	def clone(cls, loc: str, addr: str) -> 'GitFolder':
		cls.call(['clone', addr], root=loc)
		name = re.search('/(?P<name>[^/]+)\.git$', addr).group('name')
		return cls.setRoot(loc + os.sep + name)

	@classmethod
	def checkout(cls, name: str) -> 'GitFolder':
		cls._verifyRoot()
		cls.call(['checkout', name])
		return GitFolder(cls.root)

	@classmethod
	def setRoot(cls, root: str) -> 'GitFolder':
		if root is '':
			raise Exception('Using the current directory is currently not supported')
		cls.root = root
		from .gitfs import GitFolder
		folder = GitFolder(root)
		folder.status()	# Check if the root is a git repository
		return folder
		
	@classmethod
	def call(cls, cmds:List[str], root=None, killOnError=True) -> str:
		try:
			if not root:
				cls._verifyRoot()
				root = cls.root
			return subprocess.check_output(['git'] + cmds, stderr=subprocess.STDOUT, cwd=root).decode()
		except subprocess.CalledProcessError as e:
			if killOnError:
				print(e.cmd, e.output.decode())
				exit(-1)
			else:
				return e.output.decode()
			
	@classmethod
	def registerCommit(cls, commit: Commit) -> None:
		if not commit.sha in cls._commits:
			cls._commits[commit.sha] = commit
	
	@classmethod
	def getCommit(cls, sha: str) -> Commit:
		if not sha:
			raise Exception('Invalid sha \'%s\''%sha)
		if sha in cls._commits:
			return cls._commits[sha]
		else:
			commit = Commit(sha)
			cls._commits[sha] = commit
			return commit

	@classmethod
	def hasCommit(cls, sha: str) -> bool:
		return sha in cls._commits

	
	@classmethod
	def authors(cls) -> List[Author]:
		print(cls._authors)
		return cls._authors.values()
		
	@classmethod
	def getAuthor(cls, name: str, email='') -> Author:
		name = name.strip()
		if not name in cls._authors:
			if email:
				cls._authors[name] = Author(name, email)
			else:
				raise Exception('Author <%s> not known, did you load all commits (as you are reading from cached values)?'%name)
		return cls._authors[name]
	
	@classmethod
	def getTags(cls):
		'''
		Get a list of all the tags of this project. 
		These tags can directly be passed to 'Git.getTag()'
		'''
		if 	cls._tags is None:
			cls._tags = {}
			out = cls.call(['show-ref', '--tags'], killOnError=False)		# A repo without tags gives an error
			matcher = re.finditer('(?P<commit>[0-9a-z]+) refs/tags/(?P<tag>.*)', out)
			for match in matcher:
				cls._tags[match.group('tag')] = cls.getCommit(match.group('commit'))
		return list(cls._tags.keys())
		
	@classmethod
	def getTag(cls, tag):
		'''
		Get the Commit associated with the given tag.
		'''
		if 	cls._tags is None:
			cls.getTags()
		return cls._tags[tag]
