from __future__ import print_function
from gitcovery import Git, Author

'''
A basic example for usage of the module.

In this example most of the core functionalities of the module are shown, including:
 - Getting the full history of the repository
 - Getting authors of commits
 - Getting the number of lines changed in a commit
 - Getting file contents at a specific point in history
 - Getting file properties of all files
'''

# root = Git.set_root('.')
root = Git.clone('/tmp', 'https://github.com/ChielBruin/Gitcovery.git')
history = root.history()

# Print the authors of the initial commits
print('Initial commits by:', ', '.join(map(lambda x: x.author.name, Git.get_initial_commits())))

# Print the number of lines changed in the most recent commit
print('Lines changed in last commit:', len(history[0].changes()))

# Print the contents of the README file 6 commits ago
print(root.get_file('README.md').at(history[6]))

# Print the number of commits in both the full history and the history of the README file
print('The full history contains %d commits, this contains %d changes in the README file.' % (len(root.history()), len(root.get_file('README.md').history())))

# For each commit print the hash, lines added, lines removed, lines changed and title
for commit in history:
    diff = commit.changes()
    print('%s: +%d, -%d\t(%d)\t%s' % (commit.sha, diff.num_added(), diff.num_removed(), len(diff), commit.title))

# Print the number of commits made by 'Chiel Bruin'
print(len(Author.get_author('Chiel Bruin').commits))

# Print the status and relative path of each file
root.for_each_file(lambda x: print(x.status(), x.relative_path))
