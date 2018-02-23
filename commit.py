import gitfs


class Commit:
	def __init__(self, sha: str) -> None:
		self.sha = sha
		
	def pr(self) -> str:
		return gitfs.Git.call(['log', '-n', '1', str(self.sha)])
