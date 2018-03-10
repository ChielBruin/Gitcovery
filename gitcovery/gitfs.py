import os, re
from .git import Git
from .commit import Commit


class AbsGitFile(object):
	_REGEX_LINESPLIT = re.compile('\n\s*')
	
	def __init__(self, path):
		assert os.path.exists(path) is True, 'The file %s does not exist'%path
		if os.sep in path:
			idx = len(path) - 1 - path[::-1].index('/')
			self._path = path[:idx]
			self.name = path[idx+1:]
		else:
			self._path = ''
			self.name = path

	@property
	def path(self):
		if self._path:
			return self._path + os.sep + self.name
		else:
			return self.name
			
	@property
	def relativePath(self):
		'''
		Get the path relative to the repository root
		'''
		if self._path:
			return (self._path + os.sep + self.name).replace(Git.root if Git.root.endswith('/') else Git.root + '/', '')
		else:
			return self.name
	
	@property
	def parent(self):
		return GitFolder(self._path[:-1]) if os.sep in self._path else None
	
	def forEachFile(self, lamb):
		raise Exception('Method not implemented for class')
	
	def getFile(self, path):
		raise Exception('Method not implemented for class')
	
	def getFolder(self, path):
		raise Exception('Method not implemented for class')
	
	def get(self, path):
		raise Exception('Method not implemented for class')
	
	def status(self):
		'''
		Get a string representing the status of the file.
		The following statuses can be used: M (modified), N (new), D (removed), - (unchanged)
		When multiple statusses apply, return a concatenation of distinct statuses.
		'''
		out = Git.call(['status', self.path, '--short'])
		list = self._REGEX_LINESPLIT.split(out[1:] if out.startswith(' ') else out)[:-1]
		return ', '.join(list)

	def history(self):
		lines = Git.call(['log', '--pretty=format:"%H"', self.path]).split('\n')
		
		res = [None] * len(lines)
		for i, sha in enumerate(lines):
			res[i] = Git.getCommit(sha)
		return res

class GitFile(AbsGitFile):
	def __init__(self, path):
		super(GitFile, self).__init__(path)
		assert os.path.isfile(path) is True, '%s must be a file'%path

	def getFile(self, fpath):
		if fpath is self.name:
			return self
		else:
			raise Exception('%s is not a file'%self.name)
			
	def get(self, path):
		return self.getFile(path)
	
	def getFolder(self, path):
		raise Exception('Folders cannot be inside files')
	
	def status(self):
		status = super(GitFile, self).status()
		if not status:
			return '-'
		firstLetter = status[0]
		return 'N' if firstLetter == '?' else firstLetter
	
	def changes(self):
		return list(map(lambda commit: commit.getDiff(file=self.path), self.history()))
 
	def forEachFile(self, lamb):
		lamb(self)

	def at(self, commit):
		'''
		Get the contents of this file at the given commit.
		The argument can be either the commit hash as a string or a Commit object.
		'''
		if (type(commit) is str):
			sha = commit
		else:
			sha = commit.sha
		
		try:
			return Git.call(['show', '%s:%s'%(sha, self.relativePath)], killOnError=False)
		except:
			# File does not exist at that commit
			return ''
	
	def countAt(self, pattern, commit):
		'''
		Count the number of occurances af the pattern at the specified commit.
		'''
		return self.at(commit).count(pattern)

	def regexCountAt(self, pattern, commit):
		'''
		Count the number of occurances af the pattern at the specified commit using a regex pattern.
		This pattern can be compiled or a plain string, in the latter case it will be compiled for you (but this is a little slower).
		'''
		if type(pattern) is str:
			pattern = re.compile(pattern)

		return len(pattern.findall(self.at(commit)))
	
	def __str__(self):
		with open(self.path) as f: 
			return f.read()

class GitFolder(AbsGitFile):
	_children = {}
	_files = {}
	_folders = {}
	_gitignore = []
	
	def __init__(self, path, gitignore=[]):
		super(GitFolder, self).__init__(path)
		assert os.path.isdir(path) is True, '%s must be a folder'%path
		
		self._children = {}
		self._files = {}
		self._folders = {}
		self._gitignore = gitignore + ['\.git']
		self._REGEX_GITIGNORE = re.compile('\Z|'.join(self._gitignore))
	
	def _appendGitignore(self):
		with open(self.path + os.sep + '.gitignore') as f:  
			for line in f.read().split('\n'):
				if line:
					line = line.replace('.', '\.').replace('*', '.*')
					self._gitignore.append(line[:-1] if line.endswith(os.sep) else line)
			
	@property
	def children(self):
		if not self._children:
			files = os.listdir(self.path)
			if '.gitignore' in files:
				self._appendGitignore()

			for f in files:
				fname = self.path + os.sep + f
				if self._REGEX_GITIGNORE.search(f):
					continue
				if os.path.isdir(fname):
					folder = GitFolder(fname, gitignore=self._gitignore)
					self._children[f] = folder
					self._folders[f] = folder				
				else:
					fil = GitFile(fname)
					self._children[f] = fil
					self._files[f] = fil
		return self._children
		
	@property
	def files(self):
		if not self._files:
			self.children
		return self._files
		
	@property
	def folders(self):
		if not self._folders:
			self.children
		return self._folders
		
	def __getattr__(self, name):
		if name in self.folders:
			return self.folders[name]
		raise Exception('Folder %s not found'%name)
	
	def status(self):
		status = super(GitFolder, self).status()
		if not status:
			return '-'
		firstLetters = map(lambda x: x[0], status.split(', '))
		return ''.join(set(map(lambda l: 'N' if l == '?' else l, firstLetters)))

	def get(self, fpath):
		if os.sep in fpath:
			folder = fpath[:fpath.index(os.sep)]
			if folder in self.children:
				return self.children[folder].get(fpath[fpath.index(os.sep)+1:])
		else:
			if fpath in self.children:
				return self.children[fpath]
		raise Exception('File %s%s%s not found'%(self.path, os.sep, fpath))

	def getFile(self, path):
		f = self.get(path)
		if type(f) is GitFile:
			return f
		else:
			raise Exception('%s is not a file'%path)
			
	def getFolder(self, path):
		f = self.get(path)
		if type(f) is GitFolder:
			return f
		else:
			raise Exception('%s is not a folder'%path)
		
	def forEachFile(self, lamb):
		for fname in self.children:
			self.children[fname].forEachFile(lamb)

	def __str__(self):
		return ', '.join(list(map(lambda x: x + '/', self.folders.keys())) + list(self.files.keys()))
