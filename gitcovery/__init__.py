from .git import Git
from .author import Author
from .commit import Commit
from .diff import Diff, FileDiff
from .gitfs import GitFile, GitFolder

"""
**TODO** Introduction here
"""

""" General workflow
When working with this module, you always need to start by setting the root of the repository.
This can be done in two ways:
- Use an existing directory `root = Git.set_root(<path>)`
- Clone the repository `root = Git.clone(<clone_to>, <clone_from>)`

With the root set, you can also change the current version using a checkout on a branch, tag or specific commit.
This is done by calling `root = Git.checkout(<version>)`. Note that this invalidates the previous root and its children.

With the root of the repository selected there are three main approaches to traversing the repository:
- File based (recommended)  
  The root object gotten in the previous step represents a folder at the root of the repository.
  With this you can traverse the file tree by getting its children, 
  or even execute a function directly for all the children.
  These files have a number of functions to get access to their history and (historic) contents.
- Author based  
  A list of all authors in the repository can be accessed via `authors = Author.list()`. 
  Besides their name and email addresses, these authors also contain all the commits made by them.
- Commit based  
  You can also start by a list of all the commits made in the repository.
  Getting this list could be done by querying the history of the root folder: `root.history()`
  Note that there is currently no direct way to do this besides this call.
"""