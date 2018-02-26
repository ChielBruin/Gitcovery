from .commit import Commit


class Author(object):
	def __init__(self, name: str, email: str):
		self.name = name
		self.email = email
		self.commits = []
		
	def registerCommit(self, commit: Commit) -> None:
		if not commit.sha in self.commits:
			self.commits.append(commit.sha)
