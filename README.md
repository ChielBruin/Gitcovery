# Gitcovery

A Python3 module that allows you to explore git repositories. It abstracts over the git system, hiding the command-line arguments behind simple function calls and objects. This makes the module useful when (for example) running analyses on git repositories.

## Installation
To install the module simply run `pip3 install .` in the root of this repository.  
Now, the module can simply be imported with 
``` python
from gitcovery import Git
```
To run the tests for the module run: `python3 setup.py test`

## Usage
This module wraps the git repository in the following ways, making it simple to get data from it without parsing the commandline. Note that functions related to getting the diffs(`changes()`) are not fully implemented

```python
git = Git.setRoot('path/to/repo')                                       # Select local dir
git = Git.clone('/tmp', 'https://github.com/ChielBruin/Gitcovery.git')  # Clone and select remote dir
git = Git.checkout('<branch>')
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

For more examples see `example.py`

## Future work
- Improve the implementation for diffs  
  It now only contains the raw diff for each file, lacking the desired level of abstraction
- Add tests
