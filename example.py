from gitcovery import Git


folder = Git.setRoot('.')
#folder = Git.clone('/tmp', 'https://github.com/ChielBruin/Gitcovery.git')


history = folder.history()
print(history[0].changes())
print(folder.get('README.md').at(history[0]))
print(len(folder.history()), len(folder.get('README.md').history()))

for commit in history:
	d = commit.changes()
	print('%s: +%d, -%d\t(%d)\t%s'%(commit.sha, d.numAdded(),d.numRemoved(), len(d), commit.title()))
	commit.load()

# Make sure to load all commits before getting author data
print(len(Git.getAuthor('Chiel Bruin').commits))

folder.forEachFile(lambda x: print(x.status(), x.path))
