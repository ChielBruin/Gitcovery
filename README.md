# Gitcovery
[![Build Status](https://travis-ci.org/ChielBruin/Gitcovery.svg?branch=master)](https://travis-ci.org/ChielBruin/Gitcovery)

A Python module that allows you to explore git repositories. It abstracts over the git system, hiding the command-line arguments behind simple function calls and objects. This makes the module useful when you want to run analyses on git repositories.  
As an example of its simplicity, only 6 lines of Python code are needed to create a graph that shows evolution of the number of lines in this README-file over time. This includes the two lines that are always needed to draw any graph at all. Try running `python examples/graphs.py` from the root of this repository to check it out, or take a look at the other examples in the `exmples` folder.

## Usage
This module wraps the git repository in the following ways, making it simple to get data from it without parsing the commandline output.

```python
git = Git.set_root('path/to/repo')                                      # Select local dir
git = Git.clone('/tmp', 'https://github.com/ChielBruin/Gitcovery.git')  # Clone and select remote dir
git = Git.checkout('<branch>')
commit = Commit.get_commit('<commitHash>')

# Get the files in the tests folder
folder = git.get_folder('src/tests').children()
folder = git.src.tests.children()               # Functionally equivalent

# Get the author of the latest commit
print(git.history()[0].author())

# Get changes made to a file in the last commit
print(git.get_file('README.md').history()[0].changes(file='README.md'))
print(git.get_file('README.md').history()[0].changes().get_file('README.md'))
print(git.get_file('README.md').changes()[0])

# Compare the length of the full history with the length of that of the 'README.md' file
print(len(git.history()), len(git.get('README.md').history()))

# Get the status of a file
print(folder.get_file('a/file.txt').status())

# Print the name of all the files
git.for_each_file(lambda x: print(x.path))
```

## Installation
To install the module simply run `pip install .` in the root of this repository.  
Now, the module can simply be imported with 
``` python
from gitcovery import Git
```
To run the tests for the module run: `python setup.py test`

## Future work
- Improve the implementation for diffs  
  It now only records the metadata, making it impossible to reconstruct a file using all the Diffs in his history (except for its size).
- Add tests
- More documentation
- More examples
