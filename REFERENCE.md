# Gitcovery reference documentation
**\[Generated for gitcovery version 0.3\]**

> ### This reference file is currently in BETA
> Therefore, there are a few known issues and future improvements:
> - Public fields are not shown
> - Inherited functions do not show correctly (or at all)
> - Inherited docs are not shown
> - Argument descriptors are not formatted


**TODO** Introduction here

## General workflow
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
  When working with many commits, the speed of the interface with git can become a bottleneck,
  in this case you might want to consider pre-loading all the data.
  This can be done using `Commit.load_all()`.
  
You must also note that you never have to use an constructor explicitly: 
- Files can be accessed via the root of the repository
- Commits can be 'created' via `Commit.get_commit(<commit_hash>)`
- Authors are accessible by name via `Author.get_author(<name>)`
## Class overview

### Author

A commit author.
Stores the name and email of the author alongside with all the commits that are known to be of this author.

This class also keeps a static cache of all the authors in the repository.


##### `list()`

Get a list of all authors from the repository.

- :rtype: List\[Author\]
- :return: A list of all authors

##### `register_commit(commit)`

Register a commit to this author.

- :type commit: Commit
- :param commit: The commit to register
- :rtype: bool
- :return: True when registration was successful, False otherwise

##### `register_email(email)`

Register a email address to this author.

- :type email: str
- :param email: The commit to register
- :rtype: bool
- :return: True when registration was successful, False otherwise

### BlobDiff

Class representing a code blob in the diff of a file.


##### `__len__()`

Get the number of changed lines in this diff.

- :rtype: int
- :return: The number of changed lines in this diff

##### `num_added()`

Get the number of added lines in this diff.

- :rtype: int
- :return: The number of added lines

##### `num_removed()`

Get the number of removed lines in this diff.

- :rtype: int
- :return: The number of removed lines


### Commit

Class representing a commit.
A commit stores all the relevant data on a commit like the author,
the date of the commit, the commit message and the diff.


##### `__eq__(other)`

Two Commits are equal when their hashes match.

- :type other: object
- :param other: The object to compare with
- :rtype: bool
- :return: True when they are equal, False otherwise

##### `__lt__(other)`

Compare this commit with another based on the date of the commit.

- :type other: Commit
- :param other: The object to compare to
- :rtype: bool
- :return: True when this commit is older than the given commit, False otherwise

##### `author()`
- :rtype: Author
- :return: The author of this commit

##### `author_date()`
- :rtype: datetime.datetime
- :return: The author date

##### `changes(, file_name=None)`

Get the diff for this commit.
When file_name is given, only the diff for that file is returned.

- :type file_name: str
- :param file_name: Optional file name to get the diff from
- :rtype: _DiffContainer
- :return: The diff of this commit

##### `commit()`
- :rtype: Author
- :return: The commit author of this commit

##### `commit_date()`
- :rtype: datetime.datetime
- :return: The commit author date

##### `for_each_parent(func)`

Execute a function for this commit and all its parents (AKA the tree that this commit is part of).

- :type func: Commit -> None
- :param func: The function to apply for each parent recursively

##### `get_commit(sha)`

Get a commit with the given hash from the cache.
When it is not present in the cache, a new commit is created.

- :type sha: str
- :param sha: The SHA hash of the commit to get
- :rtype: Commit
- :return: The requested Commit object
- :raise: Exception, when the given hash is empty

##### `load()`

Load the data for this commit.
This function calls 'git show' and parses the output.

- :rtype: bool
- :return: True when successfully loaded, False when already loaded

##### `load_all(, load_diff=False)`

Preload all the metadata of all commits.
This method should be used when loading a large number of commits,
as a significant speedup is achieved in this case.
By default the meatadata does not include the diffs.
This is done to reduce the execution time and most notably the memory usage.
You can specify to load the diffs, but this is not recommended unless you need the diffs for all commits.

- :type load_diff: bool
- :return load_load_diff: Whether to load the diff data

##### `message()`
- :rtype: str
- :return: The commit message

##### `parents()`
- :rtype: List\[Commit\]
- :return: A list of the parents of this commit

##### `title()`
- :rtype: str
- :return: The commit title

##### `unload()`
- Unload all the cached data for this commit.

### Diff

The diff of an entire commit. This diff consists of multiple FileDiffs.



##### `add(file_diff)`

Add a file diff to this diff.

- :type file_diff: FileDiff
- :param file_diff: The file diff to add

##### `get_file(fname)`

Get the FileDiff of the file with the given name.

- :type fname: str
- :param fname: The filename to get the diff for
- :rtype: FileDiff
- :return: The FileDiff for the given file

### FileDiff

A diff for a file. This diff contains one or more diff blobs.





### Git

Main class of this module. This class represents the interface to Git,
where all other classes are data objects that represent data from Git.
It exposes a number of static methods that allow you to select or clone
the repository, do a checkout on a specific branch or make direct calls to Git.

In addition to this, the Git class also contains a cache of all the commits
and the tags in the repository and a reference to HEAD and the initial commit.


##### `checkout(name)`

Checkout a specific branch in the repository.
Calling this function is identical to calling `git checkout name` and setting the root again.
Note that previously created GitFile and GitFolder instances might be broken.
This is because files can be (re)moved on the new branch. It is therefore
advised to use the returned root to reconstruct all references.

- :type name: str
- :param name: The name of the branch to checkout
- :rtype: GitFolder
- :return: A reference to the root

##### `clone(loc, address, update=False)`

Clone a git repository to the specified location and return a reference to the root.
When there is already a folder with the correct name at that location, cloning is skipped.
Calling this function is identical to calling
`cd loc && git clone addr` and setting the root to this location.
Optionally, you could update the repository (when it already exists) by setting `update` to True.

- :type update: bool
- :param update: whether to update the repository when already cloned
- :type loc: str
- :param loc: The location to clone to
- :type address: str
- :param address: The location of the repository to clone
- :rtype: GitFolder
- :return: A reference to the root

##### `get_head()`

Get the commit associated with HEAD.

- :rtype: Commit
- :return: The commit at HEAD

##### `get_initial_commits()`

Get the initial commits of this repository.
Note that it is possible to have multiple roots, therefore a list is returned.

- :rtype: List\[Commit\]
- :return: A list of initial commits

##### `get_tag(tag)`

Get the Commit associated with the given tag.

- :type tag: str
- :param tag: The tag to get the Commit from
- :rtype: Commit
- :return The commit associated with the tag

##### `get_tags()`

Get a list of all the tags of this project.
These tags can directly be passed to 'Git.getTag(tag)'

- :rtype: List\[str\]
- :return: A list of all tags, without ordering.

##### `get_tags_by_commit()`

Get a list of all the tags and their commit in the following format:
\[(Commit, tag), ...\], this list can be sorted in chronological order using the builtin sort

- :rtype: (List\[(Commit, str)\])
- :return: A list of all tags and commits.

##### `set_root(root)`

Set the root of the repository to the specified location.
When not using the clone-function, this is the first thing you should call when using the module.
Please note that if you want to set the root to the current directory,
a . (period) is expected instead of the empty string.

- :type root: str
- :param root: The path to the root of the repository.
- :rtype: GitFolder
- :return: A reference to the root

### GitFile

A file in a git repository.
This class provides methods to get the history of a file as both a diff and a list of commits,
methods to get the contents of this file at different moments in time
and methods for running metrics on those contents.


##### `for_each_file(lamb)`

Execute a function for this file and each of its children.

- :type lamb: GitFile -> None
- :param lamb: The function to execute on each file

##### `get(path)`

Get a file that is a child of this file.
When you know that the requested file is a folder or a file,
you should use the more specific versions of this call.

- :type path: str
- :param path: The path of the file to get
- :rtype: _AbsGitFile
- :return: The file with the given path
- :raise IOError: When the file is not found

##### `get_file(path)`

Get a file that is a child of this file.

- :type path: str
- :param path: The path of the file to get
- :rtype: GitFile
- :return: The file with the given path
- :raise IOError: When the file is not found

##### `history()`

Get the history of this file as a list of commits.
These commits are stored new -> old.

- :rtype: List\[Commit\]
- :return: A list of all the commits that made changes to this file

##### `parent()`
- :rtype: GitFolder
- :return: The parent folder of this folder/file

##### `path()`
- :rtype: str
- :return: The path of the file, this can be absolute

##### `relative_path()`
- :rtype: str
- :return: The path relative to the repository root

##### `status()`

Get a string representing the status of the file.
The following statuses can be used: M (modified), N (new), D (removed), - (unchanged)
When multiple statuses apply, return a concatenation of distinct statuses.

- :rtype: str
- :return: The status of this file
##### `__len__()`

Get the length of this file in characters.
If you need the length in lines, please use the GitFile.count() functions.

- :rtype: int
- :return: The length of this file in characters

##### `__str__()`
- :rtype: str
- :return: The contents of this file

##### `at(commit)`

Get the contents of this file at the given commit.

- :type commit: Commit | str
- :param commit: The commit for which to get the corresponding file content
- :rtype: str
- :return: The content of the file

##### `changes()`
- :rtype: List\[FileDiff\]
- :return: For each of the commits in the history, the relevant part of the diff

##### `changes_from(from_commit, to_commit=None)`

Get the diff of this file between two commits.
By default this is between the HEAD and the specified commit.

- :type from_commit: Commit | str
- :param from_commit: The from commit of the diff
- :type to_commit: Commit | str
- :param to_commit: The to commit of the diff. Defaults to HEAD
- :rtype: FileDiff
- :return: The diff between the from and to commit

##### `count(pattern, at=None)`

Count the number of occurrences of the pattern in the file contents.
This function does not count using a regex, but simple string comparisons.

- :type pattern: str
- :param pattern: The pattern to count
- :type at: Commit | str
- :param at: Optional param to look at a specific version of the file
- :rtype: int
- :return: The number of times the pattern occurred

##### `regex_count(pattern, at=None)`

Count the number of occurrences of the pattern in the file contents.
This function uses a regex, and accepts both compiled and non-compiled regexes.

- :type pattern: re.RegexObject | str
- :param pattern: The pattern to count
- :type at: Commit | str
- :param at: Optional param to look at a specific version of the file
- :rtype: int
- :return: The number of times the pattern occurred

### GitFolder

A folder in a git repository.
This object contains functions to get its children (both files and other folders).
Child folders can also directly be accessed via field access, eg: `folder.get_folder('foo') == folder.foo`


##### `for_each_file(lamb)`

Execute a function for this file and each of its children.

- :type lamb: GitFile -> None
- :param lamb: The function to execute on each file

##### `get(path)`

Get a file that is a child of this file.
When you know that the requested file is a folder or a file,
you should use the more specific versions of this call.

- :type path: str
- :param path: The path of the file to get
- :rtype: _AbsGitFile
- :return: The file with the given path
- :raise IOError: When the file is not found

##### `get_file(path)`

Get a file that is a child of this file.

- :type path: str
- :param path: The path of the file to get
- :rtype: GitFile
- :return: The file with the given path
- :raise IOError: When the file is not found

##### `history()`

Get the history of this file as a list of commits.
These commits are stored new -> old.

- :rtype: List\[Commit\]
- :return: A list of all the commits that made changes to this file

##### `parent()`
- :rtype: GitFolder
- :return: The parent folder of this folder/file

##### `path()`
- :rtype: str
- :return: The path of the file, this can be absolute

##### `relative_path()`
- :rtype: str
- :return: The path relative to the repository root

##### `status()`

Get a string representing the status of the file.
The following statuses can be used: M (modified), N (new), D (removed), - (unchanged)
When multiple statuses apply, return a concatenation of distinct statuses.

- :rtype: str
- :return: The status of this file
##### `__getattr__(name)`

Get a contained folder via direct field access.

- :type name: str
- :param name: The name of the folder
- :rtype: GitFolder
- :return: The folder
- :raise IOError: When the folder is not found

##### `__str__()`
- Get the string representation of this folder.
- This consists of the names of all loders and files separated by a comma.
- :rtype: str
- :return: A string representation of this folder.

##### `children()`

Get a dictionary of all the children in this folder.
This list does not contain files excluded in the gitignore.

- :rtype: Dict\[str, GitFile\]
- :return: A dictionary containing all children

##### `files()`
- :rtype: Dict\[str, GitFile\]
- :return: All the files contained in this folder

##### `folders()`
- :rtype: Dict\[str, GitFolder\]
- :return: All the folders contained in this folder

