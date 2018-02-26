from gitcovery import Git


folder = Git.setRoot('.')
#folder = Git.clone('/tmp', 'https://github.com/ChielBruin/Gitcovery.git')

print(folder.get('README.md'))

history = folder.history()
print(history[0].changes())
print(len(folder.history()), len(folder.get('README.md').history()))

folder.forEachFile(lambda x: print(x.status(), x.path))

# Make sure to load all commits before getting author data
for commit in history:
	commit.load()

print(len(Git.getAuthor('Chiel Bruin').commits))
