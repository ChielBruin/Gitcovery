import subprocess, re, os

import gitcovery

class Git(object):
	_commits = {}
	_authors = {}
	_tags = None
	_initialCommits = []
	_head = None
	root = ''
	
	@classmethod
	def _verifyRoot(cls):
		if not cls.root:
			raise Exception('Please set the git root first')

	@classmethod
	def clone(cls, loc, addr):
		cls.call(['clone', addr], root=loc)
		name = re.search('/(?P<name>[^/]+)\.git$', addr).group('name')
		return cls.setRoot(loc + os.sep + name)

	@classmethod
	def checkout(cls, name):
		cls._verifyRoot()
		cls.call(['checkout', name])
		return GitFolder(cls.root)

	@classmethod
	def setRoot(cls, root):
		if root == '':
			raise Exception('Using the current directory is currently not supported')
		cls.root = root
		folder = gitcovery.GitFolder(root)
		folder.status()	# Check if the root is a git repository
		return folder
		
	@classmethod
	def call(cls, cmds, root=None, killOnError=True):
		try:
			if not root:
				cls._verifyRoot()
				root = cls.root
			return subprocess.check_output(['git'] + cmds, stderr=subprocess.STDOUT, cwd=root).decode('utf-8')
		except subprocess.CalledProcessError as e:
			if killOnError:
				print(e.cmd, e.output.decode())
				exit(-1)
			else:
				return e.output.decode()
			
	@classmethod
	def registerCommit(cls, commit):
		if not commit.sha in cls._commits:
			cls._commits[commit.sha] = commit
	
	@classmethod
	def getCommit(cls, sha):
		if not sha:
			raise Exception('Invalid sha \'%s\''%sha)
		if sha in cls._commits:
			return cls._commits[sha]
		else:
			commit = gitcovery.Commit(sha)
			cls._commits[sha] = commit
			return commit

	@classmethod
	def hasCommit(cls, sha):
		return sha in cls._commits

	
	@classmethod
	def authors(cls):
		return cls._authors.values()
		
	@classmethod
	def getAuthor(cls, name, email=''):
		name = name.strip()
		if not name in cls._authors:
			if email:
				cls._authors[name] = gitcovery.Author(name, email)
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
	def getTagsByCommit(cls):
		'''
		Get a list of all the tags and their commit in the following format:
		[(Commit, tag), ...]
		'''
		if 	cls._tags is None:
			cls.getTags()
		return list(map(lambda tag: (cls._tags[tag], tag), cls._tags.keys()))
		
	@classmethod
	def getTag(cls, tag):
		'''
		Get the Commit associated with the given tag.
		'''
		if 	cls._tags is None:
			cls.getTags()
		return cls._tags[tag]

	@classmethod
	def getInitialCommits(cls):
		'''
		Get the initial commits of this repository.
		Note that it is possible to have multiple roots, therefore a list is returned.
		'''
		if not cls._initialCommits:
			out = cls.call(['rev-list',  '--max-parents=0', 'HEAD'])
			cls._initialCommits = map(lambda x: cls.getCommit(x), out.split('\n')[0:-1])
		return cls._initialCommits

	@classmethod
	def getHead(cls):
		'''
		Get the commit associated with HEAD.
		'''
		if not cls._head:
			out = cls.call(['rev-parse', 'HEAD'])
			cls._head = Git.getCommit(out.trim())
		return cls._head
