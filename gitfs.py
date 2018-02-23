import subprocess, os
from typing import Dict, List

from commit import Commit


class Git(object):
	def __init__(self, path: str) -> None:
		assert os.path.exists(path) is True, 'The file %s does not exist'%path
		if os.sep in path:
			idx = len(path) - 1 - path[::-1].index('/')
			self._path = path[:idx]
			self.name = path[idx+1:]
		else:
			self._path = ''
			self.name = path
			
	@classmethod
	def _verifyRoot(cls):
		if not cls.root:
			raise Exception('Please set the git root first')

	@classmethod
	def setRoot(cls, root: str) -> 'GitFolder':
		if root is '':
			raise Exception('Using the current directory is currently not supported')
		cls.root = root
		folder = GitFolder(root)
		folder.status()	# Check if the root is a git repository
		return folder
		
	@classmethod
	def call(cls, cmds:List[str]) -> str:
		cls._verifyRoot()
		
		try:
			return subprocess.check_output(['git'] + cmds, stderr=subprocess.STDOUT, cwd=cls.root).decode()
		except subprocess.CalledProcessError as e:
			print(e.cmd, e.output.decode())
			exit(-1)

	@property
	def path(self) -> str:
		if self._path:
			return self._path + os.sep + self.name
		else:
			return self.name
	
	@property
	def parent(self) -> 'GitFolder'	:
		return GitFolder(self._path[:-1]) if os.sep in self._path else None
	
	def forEachFile(self, lamb):
		raise Exception('Method not implemented for class')
	
	def get(self, path: str) -> 'GitFile':
		raise Exception('Method not implemented for class')
	
	def status(self) -> str:
		return self.call(['status', self.path, '--short'])

	def history(self) -> List[Commit]:
		lines = self.call(['log', '--pretty=format:"%H"', self.path]).split('\n')
		return list(map(lambda h: Commit(h.replace('"', '')), lines))	



class GitFile(Git):
	def __init__(self, path: str) -> None:
		super(GitFile, self).__init__(path)
		assert os.path.isfile(path) is True, '%s must be a file'%path

	def get(self, fpath:str) -> 'GitFile':
		if fpath is self.name:
			return self
		else:
			raise Exception('%s is not a folder'%self.name)
	
	def forEachFile(self, lamb):
		lamb(self)



class GitFolder(Git):
	_children = {}
	_files = {}
	_folders = {}
	
	def __init__(self, path: str) -> None:
		super(GitFolder, self).__init__(path)
		assert os.path.isdir(path) is True, '%s must be a folder'%path
			
	@property
	def children(self) -> Dict[str, Git]:
		if not self._children:
			for f in os.listdir(self.path):
				fname = self.path + os.sep + f
				if os.path.isdir(fname):
					folder = GitFolder(fname)
					self._children[f] = folder
					self._folders[f] = folder				
				else:
					fil = GitFile(fname)
					self._children[f] = fil
					self._files[f] = fil
		return self._children
		
	@property
	def files(self) -> Dict[str, GitFile]:
		if not self._files:
			self.children
		return self._files
		
	@property
	def folders(self) -> Dict[str, 'GitFolder']:
		if not self._folders:
			self.children
		return self._folders
		
	def __getattr__(self, name: str) -> 'GitFolder':
		if name in self.folders:
			return self.folders[name]
		raise Exception('Folder %s not found'%name)
		
	def get(self, fpath: str) -> GitFile:
		if os.sep in fpath:
			folder = fpath[:fpath.index(os.sep)]
			if folder in self.children:
				return self.children[folder].get(fpath[fpath.index(os.sep)+1:])
		else:
			if fpath in self.children:
				return self.children[fpath]
		raise Exception('File %s%s%s not found'%(self.path, os.sep, fpath))

	def forEachFile(self, lamb):
		for fname in self.children:
			self.children[fname].forEachFile(lamb)

