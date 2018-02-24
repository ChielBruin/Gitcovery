# Gitcovery

Proof of concept of a Python module that allows you to explore git repositories.
It abstracts over the git system, making it useful when (for example) running analyses on repositories.

## Usage
This module wraps the git repository in the following ways, making it simple to get data from it without parsing the commandline. Note that functions related to getting the diffs(`changes()`) are not fully implemented

```python
git = Git.setRoot('path/to/repo')
commit = Git.getCommit('<commitHash>')

# Get the files in the tests folder
folder = git.get('src/tests').children()
folder = git.src.tests.children()           # Functionally equivalent

# Get the author of the latest commit
print(git.history()[0].author())

# Get changes made to a file in the last commit
print(git.get('README.md').history()[0].changes(file='README.md'))
print(git.get('README.md').history()[0].changes().getFile('README.md'))
print(git.get('README.md').changes()[0])

# Compare the length of the full history with the length of that of the 'README.md' file
print(len(git.history()), len(git.get('README.md').history()))

# Get the status of a file
print(folder.get('a/file.txt').status())

# Print the name of all the files
git.forEachFile(lambda x: print(x.path))
```

## Future work
- Make it an actual module
- Add the implementation for diffs
- Exclude files in .gitignores
- Improve the status output
- Add tests
