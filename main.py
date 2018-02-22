import os, subprocess

	
class Git:
	root = None
	
	@classmethod
	def setRoot(cls, root):
		if root is '':
			raise Exception('Using the current directory is currently not supported')
		cls.root = root
		folder = Folder(root)
		folder.status()	# Check if the root is a git repository
		return folder
		
	@classmethod
	def call(cls, cmds):
		if not cls.root:
			raise Exception('Please set the git root first')
		
		try:
			return subprocess.check_output(['git'] + cmds, stderr=subprocess.STDOUT, cwd=cls.root).decode()
		except subprocess.CalledProcessError as e:
			print(e.cmd, e.output.decode())
			exit(-1)


class GitFile(object):	
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
			return self._path +os.sep + self.name
		else:
			return self.name
	
	@property
	def parent(self):
		return Folder(self._path[:-1]) if os.sep in self._path else None
		
	def status(self):
		return Git.call(['status', self.path, '--short'])

	def history(self):
		lines = Git.call(['log', '--pretty=format:"%H"', self.path]).split('\n')
		return list(map(lambda h: Commit(h.replace('"', '')), lines))


class Commit:
	def __init__(self, sha):
		self.sha = sha
		
	def pr(self):
		return Git.call(['log', '-n', '1', str(self.sha)])


class Folder(GitFile):
	_children = {}
	
	def __init__(self, path):
		super(Folder, self).__init__(path)
		assert os.path.isdir(path) is True, '%s must be a folder'%path
			
	@property
	def children(self):
		if not self._children:
			for f in os.listdir(self.path):
				fname = self.path + os.sep + f
				if os.path.isdir(fname):
					self._children[f] = Folder(fname)				
				else:
					self._children[f] = File(fname)
		return self._children	
		
	def __getattr__(self, name):
		if name in self.children:
			return self.children[name]
		raise Exception('File %s not found'%name)
		
	def get(self, fpath):
		if os.sep in fpath:
			folder = fpath[:fpath.index(os.sep)]
			if folder in self.children:
				return self.children[folder].get(fpath[fpath.index(os.sep)+1:])
		else:
			if fpath in self.children:
				return self.children[fpath]
		raise Exception('File %s%s%s not found'%(self.path, os.sep, fpath))


class File(GitFile):
	def __init__(self, path):
		super(File, self).__init__(path)
		assert os.path.isfile(path) is True, '%s must be a file'%path

	def get(self, fpath):
		if fpath is self.name:
			return self
		else:
			raise Exception('%s is not a folder'%self.name)


folder = Git.setRoot('')
print(folder.history()[0].pr())
print(len(folder.history()), len(folder.get('README.md').history()))
print(folder.get('README.md').status())

