# Gitcovery reference documentation
**\[Generated for gitcovery version 0.3.3\]**


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


#### Fields
**commits (List\[Commit\])**

The commits made by this author.


**emails (List\[str\])**

The email addresses of this author.


**name (str)**

The name of the author.



#### Functions
**list() - _static_**  
Get a list of all authors from the repository.
- **`Returns`: List\[Author\]**  
    A list of all authors

**register\_commit(commit)**  
Register a commit to this author.
- **`commit`: Commit**  
    The commit to register
- **`Returns`: bool**  
    True when registration was successful, False otherwise

**register\_email(email)**  
Register a email address to this author.
- **`email`: str**  
    The commit to register
- **`Returns`: bool**  
    True when registration was successful, False otherwise

### BlobDiff

Class representing a code blob in the diff of a file.


#### Fields
**added (List\[str\])**

The lines that were added in this blob.


**changes (int)**

The number of lines changed in this blob.


**removed (List\[str\])**

The lines that were removed in this blob.



#### Functions
**\_\_len\_\_()**  
Get the number of changed lines in this diff.
- **`Returns`: int**  
    The number of changed lines in this diff

**num\_added()**  
Get the number of added lines in this diff.
- **`Returns`: int**  
    The number of added lines

**num\_removed()**  
Get the number of removed lines in this diff.
- **`Returns`: int**  
    The number of removed lines

### Commit

Class representing a commit.
A commit stores all the relevant data on a commit like the author,
the date of the commit, the commit message and the diff.


#### Fields
**author (Author)**

The author of this commit


**author_date (datetime.datetime)**

The author date


**commit (Author)**

The commit author of this commit


**commit_date (datetime.datetime)**

The commit author date


**message (str)**

The commit message


**parents (List\[Commit\])**

A list of the parents of this commit


**sha (str)**

The SHA hash of the commit.


**title (str)**

The commit title



#### Functions
**\_\_eq\_\_(other)**  
Two Commits are equal when their hashes match.
- **`other`: object**  
    The object to compare with
- **`Returns`: bool**  
    True when they are equal, False otherwise

**\_\_lt\_\_(other)**  
Compare this commit with another based on the date of the commit.
- **`other`: Commit**  
    The object to compare to
- **`Returns`: bool**  
    True when this commit is older than the given commit, False otherwise

**changes(, file\_name=None)**  
Get the diff for this commit.
When file_name is given, only the diff for that file is returned.
- **`file_name`: str**  
    Optional file name to get the diff from
- **`Returns`: _DiffContainer**  
    The diff of this commit

**for\_each\_parent(func)**  
Execute a function for this commit and all its parents (AKA the tree that this commit is part of).
- **`func`: Commit -> None**  
    The function to apply for each parent recursively

**get\_commit(sha) - _static_**  
Get a commit with the given hash from the cache.
When it is not present in the cache, a new commit is created.
- **`sha`: str**  
    The SHA hash of the commit to get
- **`Returns`: Commit**  
    The requested Commit object

**load()**  
Load the data for this commit.
This function calls 'git show' and parses the output.
- **`Returns`: bool**  
    True when successfully loaded, False when already loaded

**load\_all(, load\_diff=False) - _static_**  
Preload all the metadata of all commits.
This method should be used when loading a large number of commits,
as a significant speedup is achieved in this case.
By default the meatadata does not include the diffs.
This is done to reduce the execution time and most notably the memory usage.
You can specify to load the diffs, but this is not recommended unless you need the diffs for all commits.
- **`load_diff`: bool**  
    Whether to load the diff data

**unload()**  
Unload all the cached data for this commit.


### Diff

The diff of an entire commit. This diff consists of multiple FileDiffs.


#### Fields
**data (Dict\[str, FileDiff\])**

The files and their diffs stored in this diff



#### Functions
**\_\_len\_\_()**  
Get the number of changed lines in this diff.
- **`Returns`: int**  
    The number of changed lines in this diff

**add(file\_diff)**  
Add a file diff to this diff.
- **`file_diff`: FileDiff**  
    The file diff to add

**get\_file(fname)**  
Get the FileDiff of the file with the given name.
- **`fname`: str**  
    The filename to get the diff for
- **`Returns`: FileDiff**  
    The FileDiff for the given file

**num\_added()**  
Get the number of added lines in this diff.
- **`Returns`: int**  
    The number of added lines

**num\_removed()**  
Get the number of removed lines in this diff.
- **`Returns`: int**  
    The number of removed lines

### FileDiff

A diff for a file. This diff contains one or more diff blobs.


#### Fields
**name (str)**

The name of the file.



#### Functions
**\_\_len\_\_()**  
Get the number of changed lines in this diff.
- **`Returns`: int**  
    The number of changed lines in this diff

**num\_added()**  
Get the number of added lines in this diff.
- **`Returns`: int**  
    The number of added lines

**num\_removed()**  
Get the number of removed lines in this diff.
- **`Returns`: int**  
    The number of removed lines

### Git

Main class of this module. This class represents the interface to Git,
where all other classes are data objects that represent data from Git.
It exposes a number of static methods that allow you to select or clone
the repository, do a checkout on a specific branch or make direct calls to Git.

In addition to this, the Git class also contains a cache of all the commits
and the tags in the repository and a reference to HEAD and the initial commit.


#### Fields
**root (GitFolder) - _static_**

The root of the repository, `None` when the root is not set.



#### Functions
**checkout(name) - _static_**  
Checkout a specific branch in the repository.
Calling this function is identical to calling `git checkout name` and setting the root again.
Note that previously created GitFile and GitFolder instances might be broken.
This is because files can be (re)moved on the new branch. It is therefore
advised to use the returned root to reconstruct all references.
- **`name`: str**  
    The name of the branch to checkout
- **`Returns`: GitFolder**  
    A reference to the root

**clone(loc, address, update=False) - _static_**  
Clone a git repository to the specified location and return a reference to the root.
When there is already a folder with the correct name at that location, cloning is skipped.
Calling this function is identical to calling
`cd loc && git clone addr` and setting the root to this location.
Optionally, you could update the repository (when it already exists) by setting `update` to True.

Note that this function only works for **public** repositories.
- **`update`: bool**  
    whether to update the repository when already cloned
- **`loc`: str**  
    The location to clone to
- **`address`: str**  
    The location of the repository to clone
- **`Returns`: GitFolder**  
    A reference to the root

**get\_decode\_settings() - _static_**  
Get the settings of the decoder for raw git output.
See https://docs.python.org/2/library/codecs.html#codec-base-classes for valid error policies.
- **`Returns`: (str, str)**  
    A tuple containing the encoding and error policy

**get\_head() - _static_**  
Get the commit associated with HEAD.
- **`Returns`: Commit**  
    The commit at HEAD

**get\_initial\_commits() - _static_**  
Get the initial commits of this repository.
Note that it is possible to have multiple roots, therefore a list is returned.
- **`Returns`: List\[Commit\]**  
    A list of initial commits

**get\_tag(tag) - _static_**  
Get the Commit associated with the given tag.
- **`tag`: str**  
    The tag to get the Commit from
- **`Returns`: Commit**  
    The commit associated with the tag

**get\_tags() - _static_**  
Get a list of all the tags of this project.
These tags can directly be passed to 'Git.getTag(tag)'
- **`Returns`: List\[str\]**  
    A list of all tags, without ordering.

**get\_tags\_by\_commit() - _static_**  
Get a list of all the tags and their commit in the following format:
\[(Commit, tag), ...\], this list can be sorted in chronological order using the builtin sort
- **`Returns`: (List\[(Commit, str)\])**  
    A list of all tags and commits.

**set\_root(root) - _static_**  
Set the root of the repository to the specified location.
When not using the clone-function, this is the first thing you should call when using the module.
Please note that if you want to set the root to the current directory,
a . (period) is expected instead of the empty string.
- **`root`: str**  
    The path to the root of the repository.
- **`Returns`: GitFolder**  
    A reference to the root

**update() - _static_**  
Update the repository tho the latest version on the current branch.
The effects are the same as calling `git fetch --all && git pull`.

Note that this function only works for **public** repositories.
- **`Returns`: GitFolder**  
    The root of the repository

### GitFile

A file in a git repository.
This class provides methods to get the history of a file as both a diff and a list of commits,
methods to get the contents of this file at different moments in time
and methods for running metrics on those contents.


#### Fields
**name (str)**

The name of this file.


**path (str)**

The path of the file, this can be absolute


**relative_path (str)**

The path relative to the repository root



#### Functions
**\_\_len\_\_()**  
Get the length of this file in characters.
If you need the length in lines, please use the GitFile.count() functions.
- **`Returns`: int**  
    The length of this file in characters

**\_\_str\_\_()**  
- **`Returns`: str**  
    The contents of this file

**at(commit)**  
Get the contents of this file at the given commit.
- **`commit`: Commit | str**  
    The commit for which to get the corresponding file content
- **`Returns`: str**  
    The content of the file

**changes()**  
- **`Returns`: List\[FileDiff\]**  
    For each of the commits in the history, the relevant part of the diff

**changes\_from(from\_commit, to\_commit=None)**  
Get the diff of this file between two commits.
By default this is between the HEAD and the specified commit.
- **`from_commit`: Commit | str**  
    The from commit of the diff
- **`to_commit`: Commit | str**  
    The to commit of the diff. Defaults to HEAD
- **`Returns`: FileDiff**  
    The diff between the from and to commit

**count(pattern, at=None)**  
Count the number of occurrences of the pattern in the file contents.
This function does not count using a regex, but simple string comparisons.
- **`pattern`: str**  
    The pattern to count
- **`at`: Commit | str**  
    Optional param to look at a specific version of the file
- **`Returns`: int**  
    The number of times the pattern occurred

**for\_each\_file(lamb)**  
Execute a function for this file and each of its children.
- **`lamb`: GitFile -> None**  
    The function to execute on each file

**get(path)**  
Get a file that is a child of this file.
When you know that the requested file is a folder or a file,
you should use the more specific versions of this call.
- **`path`: str**  
    The path of the file to get
- **`Returns`: _AbsGitFile**  
    The file with the given path
- **`Raises`: IOError**  
    When the file is not found

**get\_file(path)**  
Get a file that is a child of this file.
- **`path`: str**  
    The path of the file to get
- **`Returns`: GitFile**  
    The file with the given path
- **`Raises`: IOError**  
    When the file is not found

**history()**  
Get the history of this file as a list of commits.
These commits are stored new -> old.
- **`Returns`: List\[Commit\]**  
    A list of all the commits that made changes to this file

**parent()**  
- **`Returns`: GitFolder**  
    The parent folder of this folder/file

**regex\_count(pattern, at=None)**  
Count the number of occurrences of the pattern in the file contents.
This function uses a regex, and accepts both compiled and non-compiled regexes.
- **`pattern`: re.RegexObject | str**  
    The pattern to count
- **`at`: Commit | str**  
    Optional param to look at a specific version of the file
- **`Returns`: int**  
    The number of times the pattern occurred

**status()**  
Get a string representing the status of the file.
The following statuses can be used: M (modified), N (new), D (removed), - (unchanged)
When multiple statuses apply, return a concatenation of distinct statuses.
- **`Returns`: str**  
    The status of this file

### GitFolder

A folder in a git repository.
This object contains functions to get its children (both files and other folders).
Child folders can also directly be accessed via field access, eg: `folder.get_folder('foo') == folder.foo`


#### Fields
**name (str)**

The name of this file.


**path (str)**

The path of the file, this can be absolute


**relative_path (str)**

The path relative to the repository root



#### Functions
**\_\_getattr\_\_(name)**  
Get a contained folder via direct field access.
- **`name`: str**  
    The name of the folder
- **`Returns`: GitFolder**  
    The folder
- **`Raises`: IOError**  
    When the folder is not found

**\_\_str\_\_()**  
Get the string representation of this folder.
This consists of the names of all loders and files separated by a comma.
- **`Returns`: str**  
    A string representation of this folder.

**children()**  
Get a dictionary of all the children in this folder.
This list does not contain files excluded in the gitignore.
- **`Returns`: Dict\[str, GitFile\]**  
    A dictionary containing all children

**files()**  
- **`Returns`: Dict\[str, GitFile\]**  
    All the files contained in this folder

**folders()**  
- **`Returns`: Dict\[str, GitFolder\]**  
    All the folders contained in this folder

**for\_each\_file(lamb)**  
Execute a function for this file and each of its children.
- **`lamb`: GitFile -> None**  
    The function to execute on each file

**get(path)**  
Get a file that is a child of this file.
When you know that the requested file is a folder or a file,
you should use the more specific versions of this call.
- **`path`: str**  
    The path of the file to get
- **`Returns`: _AbsGitFile**  
    The file with the given path
- **`Raises`: IOError**  
    When the file is not found

**get\_file(path)**  
Get a file that is a child of this file.
- **`path`: str**  
    The path of the file to get
- **`Returns`: GitFile**  
    The file with the given path
- **`Raises`: IOError**  
    When the file is not found

**history()**  
Get the history of this file as a list of commits.
These commits are stored new -> old.
- **`Returns`: List\[Commit\]**  
    A list of all the commits that made changes to this file

**parent()**  
- **`Returns`: GitFolder**  
    The parent folder of this folder/file

**status()**  
Get a string representing the status of the file.
The following statuses can be used: M (modified), N (new), D (removed), - (unchanged)
When multiple statuses apply, return a concatenation of distinct statuses.
- **`Returns`: str**  
    The status of this file

