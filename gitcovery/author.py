class Author(object):
	def __init__(self, name, email):
		self.name = name
		self.email = email
		self.commits = []
		
	def registerCommit(self, commit):
		if not commit.sha in self.commits:
			self.commits.append(commit.sha)
