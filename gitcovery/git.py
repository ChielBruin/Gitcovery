import subprocess, re, os

import gitcovery

class Git(object):
	'''
	Main class of this module. This class represents the interface to Git, 
	where all other classes are data objects that represent data from Git.
	It exposes a number of static methods that allow you to select or clone 
	the repository, do a checkout on a specific branch or make direct calls to Git.
	
	In addition to this, the Git class also contains a cache of all the commmits
	and authors, the tags in the repository and a reference to HEAD and the initial commit. 
	'''
	_commits = {}
	_authors = {}
	_tags = None
	_initialCommits = []
	_head = None
	root = ''
	
	@classmethod
	def _verifyRoot(cls):
		'''
		Verify that the root is set, otherwise throws an exception.
		This does not validate the root, as this is done when setting the root.
		'''
		if not cls.root:
			raise Exception('Please set the git root first')

	@classmethod
	def clone(cls, loc, addr):
		'''
		Clone a git repository to the specified location and return a reference to the root.
		Calling this function is identical to calling 
		`cd loc && git clone addr` and setting the root to this location.
		
		@param loc: (str) The location to clone to
		@param addr: (str) The location of the repository to clone
		@return (GitFolder) A reference to the root
		'''
		cls.call(['clone', addr], root=loc)
		name = re.search('/(?P<name>[^/]+)\.git$', addr).group('name')
		return cls.setRoot(loc + os.sep + name)

	@classmethod
	def checkout(cls, name):
		'''
		Checkout a specific branch in the repository.
		Calling this function is identical to calling `git checkout name` and setting the root again.
		Note that previously created GitFile and GitFolder instances might be broken.
		This is because files can be (re)moved on the new branch. It is therefore
		advised to use the returned root to reconstruct all references.
		
		@param name: (str) The name of the branch to checkout
		@return (GitFolder) A reference to the root
		'''
		cls._verifyRoot()
		cls.call(['checkout', name])
		return GitFolder(cls.root)

	@classmethod
	def setRoot(cls, root):
		'''
		Set the root of the repository to the specified location.
		When not using the clone-function, this is the first thing you should call when using the module.
		Please note that if you want to set the root to the current directory,
		a . (period) is expected instead of the empty string.
		
		@param root: (str) The path to the root of the repository.
		@return (GitFolder)	A reference to the root
		'''
		if root == '':
			# Converting this to a . is easy, but it might not be what the user wants.
			# Therefore the error is thrown containing a possible solution.
			raise Exception('Using the current directory is only supported by setting the root to \'.\'')
		cls.root = root
		folder = gitcovery.GitFolder(root)

		# Check if the root is a git repository
		try:
			folder.status()
		except Exception:
			raise Exception('%s is not a Git repository'%root)

		return folder
		
	@classmethod
	def call(cls, cmds, root=None, killOnError=True):
		'''
		Call the git subsystem via the command line and return the output.
		Kills the process when the call fails (unless specified otherwise).
		You are not encouraged to use this call directly, when you have a valid reason to do so
		you might want to consider to request a feature on GitHub.
		
		@param cmds: (List[str]) A list of arguments to pass to the command line.
			Note that 'git' is always prepended
		@param root: (str) When set uses a different working directory to run the command.
			When not specified the root of the repository is used.
		@param killOnError: (bool) Indicates whether an error should kill the process (True by default)
		'''
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
	def getCommit(cls, sha):
		'''
		Get a commit with the given hash from the cache.
		When it is not present in the cache, a new commit is created.
		
		@param sha: (str) The SHA hash of the commit to get
		@returns (Commit) The requested Commit object
		'''
		if not sha:
			raise Exception('Invalid sha \'%s\''%sha)
		if sha in cls._commits:
			return cls._commits[sha]
		else:
			commit = gitcovery.Commit(sha)
			cls._commits[sha] = commit
			return commit

	@classmethod
	def authors(cls):
		'''
		Get a list of all authors from the cache.
		Because the authors are only cached when they are encountered,
		you need to make sure that every commit that could introduce a new author is loaded.
		
		@returns (List[Author]) A list of all cached authors
		'''
		return cls._authors.values()
		
	@classmethod
	def getAuthor(cls, name, email=''):
		'''
		Get an Author object from the cache with a given name.
		When an author is not present, it is created and added to the cache (as long as an email is provided)
		The email address is not neccesary when searching, the name suffices.
		
		@param name: (str) The name of the author
		@param email: (str) The email of the author (this value is optional)
		@return (Author) The requested Author object
		'''
		name = name.strip()
		if not name in cls._authors:
			if email:
				cls._authors[name] = gitcovery.Author(name, email)
			else:
				raise Exception('Author <%s> not known, did you load all commits (as you are reading from cached values)?'%name)
		
		#TODO: Check the email and add it if email is unknown for that author
		return cls._authors[name]
	
	@classmethod
	def getTags(cls):
		'''
		Get a list of all the tags of this project. 
		These tags can directly be passed to 'Git.getTag()'
		
		@return (List[str]) A list of all tags, without ordering.
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
		[(Commit, tag), ...], this list can be sorted in chronological order using the builtin sort
		
		@return (List[(Commit, str)]) A list of all tags and commits.
		'''
		if 	cls._tags is None:
			cls.getTags()
		return list(map(lambda tag: (cls._tags[tag], tag), cls._tags.keys()))
		
	@classmethod
	def getTag(cls, tag):
		'''
		Get the Commit associated with the given tag.
		
		@param tag: (str) The tag to get the Commit from
		@return (Commit) The commit associated with the tag
		'''
		if 	cls._tags is None:
			cls.getTags()
		return cls._tags[tag]

	@classmethod
	def getInitialCommits(cls):
		'''
		Get the initial commits of this repository.
		Note that it is possible to have multiple roots, therefore a list is returned.
		
		@return (List[Commit]) A list of initial commits
		'''
		if not cls._initialCommits:
			out = cls.call(['rev-list',  '--max-parents=0', 'HEAD'])
			cls._initialCommits = map(lambda x: cls.getCommit(x), out.split('\n')[0:-1])
		return cls._initialCommits

	@classmethod
	def getHead(cls):
		'''
		Get the commit associated with HEAD.
		
		@return (Commit) the commit at HEAD
		'''
		if not cls._head:
			out = cls.call(['rev-parse', 'HEAD'])
			cls._head = Git.getCommit(out.trim())
		return cls._head
