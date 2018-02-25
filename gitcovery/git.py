import subprocess
from typing import Dict, List

from .commit import Commit

class Git(object):
	_commits = {}
	
	@classmethod
	def _verifyRoot(cls):
		if not cls.root:
			raise Exception('Please set the git root first')

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
	def call(cls, cmds:List[str]) -> str:
		cls._verifyRoot()
		
		try:
			return subprocess.check_output(['git'] + cmds, stderr=subprocess.STDOUT, cwd=cls.root).decode()
		except subprocess.CalledProcessError as e:
			print(e.cmd, e.output.decode())
			exit(-1)
			
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
