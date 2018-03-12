from __future__ import print_function
from gitcovery import Git


folder = Git.setRoot('.')
#folder = Git.clone('/tmp', 'https://github.com/ChielBruin/Gitcovery.git')


print('Initial commits by:', ', '.join(map(lambda x: x.author().name, Git.getInitialCommits())))
history = folder.history()
print(history[0].changes())
print(folder.get_file('README.md').at(history[0]))
print(len(folder.history()), len(folder.get_file('README.md').history()))

for commit in history:
	d = commit.changes()
	print('%s: +%d, -%d\t(%d)\t%s' % (commit.sha, d.num_added(), d.num_removed(), len(d), commit.title()))
	commit.load()

# Make sure to load all commits before getting author data
print(len(Git.getAuthor('Chiel Bruin').commits))

folder.forEachFile(lambda x: print(x.status(), x.path))

