# Gitcovery

Proof of concept of a Python module that allows you to explore git repositories.
It abstracts over the git system, making it useful when (for example) running analyses on repositories.

## Usage
The idea is that you would be able to explore a repository in the following ways:

```python
git = Git.setRoot('path/to/repo')

# Get the files in the tests folder
folder = git.get('src/tests').children()
folder = git.src.tests.children()           # Functionally equivalent

# Get the author of the latest commit
print(git.history()[0].author())

# Get changes made to a file in the last commit
print(git.get('README.md').history()[0].changes(file='README.md'))
print(git.get('README.md').changes()[0])

# Compare the length of the full history with the length of that of the 'README.md' file
print(len(git.history()), len(git.get('README.md').history()))

# Get the status of a file
print(folder.get('a/file').status())

# Print the name of all the files
git.forEachFile(lambda x: print(x.path))
```
