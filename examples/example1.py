from __future__ import print_function
from gitcovery import Git

folder = Git.set_root('.')
# folder = Git.clone('/tmp', 'https://github.com/ChielBruin/Gitcovery.git')


print('Initial commits by:', ', '.join(map(lambda x: x.author().name, Git.get_initial_commits())))
history = folder.history()
print(history[0].changes())
print(folder.get_file('README.md').at(history[0]))
print(len(folder.history()), len(folder.get_file('README.md').history()))

for commit in history:
    diff = commit.changes()
    print('%s: +%d, -%d\t(%d)\t%s' % (commit.sha, diff.num_added(), diff.num_removed(), len(diff), commit.title()))
    commit.load()

# Make sure to load all commits before getting author data
print(len(Git.get_author('Chiel Bruin').commits))

folder.for_each_file(lambda x: print(x.status(), x.path))
