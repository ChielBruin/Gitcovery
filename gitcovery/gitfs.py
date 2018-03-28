import os
import re

from gitcovery import Commit
from .diff import FileDiff
from .git import Git


class _AbsGitFile(object):
    """
    Interface for files and folders in a git repository.
    Provides methods for getting the path, child files, history and status of a file.
    """

    # Regex for splitting a line with whitespace at the head
    _REGEX_LINESPLIT = re.compile('\n\s*')

    def __init__(self, path):
        """
        Constructor for an _AbsGitFile.
        Checks if the file exists and stores the name and path of the file.

        :type path: str
        :param path: The filepath of this file
        """
        # Make sure the file exists
        assert os.path.exists(path) is True, 'The file %s does not exist' % path

        self._path = ''
        # The name of this file.
        self.name = path  # :type: str

        if os.sep in path:
            last_sep = len(path) - 1 - path[::-1].index('/')
            self._path = path[:last_sep]
            self.name = path[last_sep + 1:]

    @property
    def path(self):
        """
        :rtype: str
        :return: The path of the file, this can be absolute
        """
        if self._path:
            return self._path + os.sep + self.name
        else:
            return self.name

    @property
    def relative_path(self):
        """
        :rtype: str
        :return: The path relative to the repository root
        """
        if self._path:
            root = Git.root.path
            return (self._path + os.sep + self.name).replace(root if root.endswith('/') else root + '/', '')
        else:
            return self.name

    def parent(self):
        """
        :rtype: GitFolder
        :return: The parent folder of this folder/file
        """
        return GitFolder(self._path[:-1]) if os.sep in self._path else None

    def for_each_file(self, lamb):
        """
        Execute a function for this file and each of its children.

        :type lamb: GitFile -> None
        :param lamb: The function to execute on each file
        """
        raise NotImplementedError()

    def get_file(self, path):
        """
        Get a file that is a child of this file.

        :type path: str
        :param path: The path of the file to get
        :rtype: GitFile
        :return: The file with the given path
        :raise IOError: When the file is not found
        """
        raise NotImplementedError()

    def get_folder(self, path):
        """
           Get a folder that is a child of this file.

           :type path: str
           :param path: The path of the folder to get
           :rtype: GitFolder
           :return: The folder with the given path
           :raise IOError: when the file is not found
           """
        raise NotImplementedError()

    def get(self, path):
        """
        Get a file that is a child of this file.
        When you know that the requested file is a folder or a file,
        you should use the more specific versions of this call.

        :type path: str
        :param path: The path of the file to get
        :rtype: _AbsGitFile
        :return: The file with the given path
        :raise IOError: When the file is not found
        """
        raise NotImplementedError()

    def status(self):
        """
        Get a string representing the status of the file.
        The following statuses can be used: M (modified), N (new), D (removed), - (unchanged)
        When multiple statuses apply, return a concatenation of distinct statuses.

        :rtype: str
        :return: The status of this file
        """
        out = Git.call(['status', self.path, '--short'], kill_on_error=False)
        return self._REGEX_LINESPLIT.split(out[1:] if out.startswith(' ') else out)[:-1]

    def history(self):
        """
        Get the history of this file as a list of commits.
        These commits are stored new -> old.

        :rtype: List[Commit]
        :return: A list of all the commits that made changes to this file
        """
        lines = Git.call(['log', '--pretty=format:%H', self.path]).split('\n')

        res = [None] * len(lines)
        for i, sha in enumerate(lines):
            res[i] = Commit.get_commit(sha)
        return res


class GitFile(_AbsGitFile):
    """
    A file in a git repository.
    This class provides methods to get the history of a file as both a diff and a list of commits,
    methods to get the contents of this file at different moments in time
    and methods for running metrics on those contents.
    """

    def __init__(self, path):
        """
        Constructor for a GitFile form its path.
        The given path must point to a valid file.

        :type path: str
        :param path: The path that points to the file
        """
        super(GitFile, self).__init__(path)
        assert os.path.isfile(path) is True, '%s must be a file' % path
        self._contents = None

    def changes(self):
        """
        :rtype: List[FileDiff]
        :return: For each of the commits in the history, the relevant part of the diff
        """
        return list(map(lambda commit: commit.getDiff(file=self.path), self.history()))

    def changes_from(self, from_commit, to_commit=None):
        """
        Get the diff of this file between two commits.
        By default this is between the HEAD and the specified commit.

        :type from_commit: Commit | str
        :param from_commit: The from commit of the diff
        :type to_commit: Commit | str
        :param to_commit: The to commit of the diff. Defaults to HEAD
        :rtype: FileDiff
        :return: The diff between the from and to commit
        """
        if isinstance(from_commit, str):
            from_commit = Commit.get_commit(from_commit)
        if to_commit is None:
            to_commit = Git.get_head()
        elif isinstance(to_commit, str):
            to_commit = Commit.get_commit(to_commit)

        assert from_commit < to_commit, 'The from commit should be older than the to commit'

        out = Git.call(['diff', from_commit, to_commit, self.relative_path])
        return FileDiff(self.name, out)

    def at(self, commit):
        """
        Get the contents of this file at the given commit.

        :type commit: Commit | str
        :param commit: The commit for which to get the corresponding file content
        :rtype: str
        :return: The content of the file
        """
        if isinstance(commit, str):
            sha = commit
        else:
            sha = commit.sha

        try:
            return Git.call(['show', '%s:%s' % (sha, self.relative_path)], kill_on_error=False)
        except IOError:
            # File does not exist at that commit
            return ''

    def count(self, pattern, at=None):
        """
        Count the number of occurrences of the pattern in the file contents.
        This function does not count using a regex, but simple string comparisons.

        :type pattern: str
        :param pattern: The pattern to count
        :type at: Commit | str
        :param at: Optional param to look at a specific version of the file
        :rtype: int
        :return: The number of times the pattern occurred
        """
        if at:
            return self.at(at).count(pattern)
        else:
            return str(self).count(pattern)

    def regex_count(self, pattern, at=None):
        """
        Count the number of occurrences of the pattern in the file contents.
        This function uses a regex, and accepts both compiled and non-compiled regexes.

        :type pattern: re.RegexObject | str
        :param pattern: The pattern to count
        :type at: Commit | str
        :param at: Optional param to look at a specific version of the file
        :rtype: int
        :return: The number of times the pattern occurred
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        if at:
            return len(pattern.findall(self.at(at)))
        else:
            return len(pattern.findall(str(self)))

    def __str__(self):
        """
        :rtype: str
        :return: The contents of this file
        """
        if not self._contents:
            with open(self.path) as f:
                self._contents = f.read()
        return self._contents

    def __len__(self):
        """
        Get the length of this file in characters.
        If you need the length in lines, please use the GitFile.count() functions.

        :rtype: int
        :return: The length of this file in characters
        """
        return len(str(self))

    def get_file(self, fpath):
        if fpath is self.name:
            return self
        else:
            raise IOError('%s is not a file' % self.name)

    def get(self, path):
        return self.get_file(path)

    def get_folder(self, path):
        raise IOError('Folders cannot be inside files')

    def status(self):
        status = super(GitFile, self).status()
        if not status:
            return '-'
        first_letter = status[0][0]
        return 'N' if first_letter == '?' else first_letter

    def for_each_file(self, lamb):
        lamb(self)


class GitFolder(_AbsGitFile):
    """
    A folder in a git repository.
    This object contains functions to get its children (both files and other folders).
    Child folders can also directly be accessed via field access, eg: `folder.get_folder('foo') == folder.foo`
    """
    _children = {}   # :type: Dict[str, _AbsGitFile]
    _files = {}      # :type: Dict[str, GitFile]
    _folders = {}    # :type: Dict[str, GitFolder]
    _gitignore = []  # :type: List[str]

    def __init__(self, path, gitignore=None):
        """
        Constructor for a GitFolder object.
        This folder must be a real folder in the repository.

        :type path: str
        :param path: The path of this folder
        :type gitignore: List[str]
        :param gitignore: A list of patterns for files to ignore
        """
        super(GitFolder, self).__init__(path)
        if gitignore is None:
            gitignore = ['\.git']
        assert os.path.isdir(path) is True, '%s must be a folder' % path

        self._children = {}
        self._files = {}
        self._folders = {}
        self._gitignore = gitignore
        self._REGEX_GITIGNORE = re.compile('\Z|'.join(self._gitignore))

    def _load_gitignore(self):
        """
        Load the gitignore file present in this folder.
        """
        with open(self.path + os.sep + '.gitignore') as f:
            for line in f.read().split('\n'):
                if line:
                    if line.startswith('!'):
                        # TODO: remove files from gitignore
                        pass
                    line = line.replace('.', '\.').replace('*', '.*')
                    self._gitignore.append(line[:-1] if line.endswith(os.sep) else line)

    def children(self):
        """
        Get a dictionary of all the children in this folder.
        This list does not contain files excluded in the gitignore.

        :rtype: Dict[str, GitFile]
        :return: A dictionary containing all children
        """
        if not self._children:
            files = os.listdir(self.path)
            if '.gitignore' in files:
                self._load_gitignore()

            for f in files:
                fname = self.path + os.sep + f
                if self._REGEX_GITIGNORE.search(f):
                    continue
                if os.path.isdir(fname):
                    folder = GitFolder(fname, gitignore=self._gitignore)
                    self._children[f] = folder
                    self._folders[f] = folder
                else:
                    fil = GitFile(fname)
                    self._children[f] = fil
                    self._files[f] = fil
        return self._children

    def files(self):
        """
        :rtype: Dict[str, GitFile]
        :return: All the files contained in this folder
        """
        if not self._files:
            self.children()
        return self._files

    def folders(self):
        """
        :rtype: Dict[str, GitFolder]
        :return: All the folders contained in this folder
        """
        if not self._folders:
            self.children()
        return self._folders

    def __getattr__(self, name):
        """
        Get a contained folder via direct field access.

        :type name: str
        :param name: The name of the folder
        :rtype: GitFolder
        :return: The folder
        :raise IOError: When the folder is not found
        """
        if name in self.folders():
            return self._folders[name]
        raise IOError('Folder %s not found' % name)

    def __str__(self):
        """
        Get the string representation of this folder.
        This consists of the names of all loders and files separated by a comma.

        :rtype: str
        :return: A string representation of this folder.
        """
        return ', '.join(list(map(lambda x: x + '/', self.folders().keys())) + list(self.files().keys()))

    def status(self):
        status = super(GitFolder, self).status()
        if not status:
            return '-'
        first_letters = map(lambda x: x[0], status)
        return ''.join(set(map(lambda letter: 'N' if letter == '?' else letter, first_letters)))

    def get(self, fpath):
        if os.sep in fpath:
            folder = fpath[:fpath.index(os.sep)]
            if folder in self.children():
                return self.children()[folder].get(fpath[fpath.index(os.sep) + 1:])
        else:
            if fpath in self.children():
                return self.children()[fpath]
        raise IOError('File %s%s%s not found' % (self.path, os.sep, fpath))

    def get_file(self, path):
        f = self.get(path)
        if isinstance(f, GitFile):
            return f
        else:
            raise IOError('%s is not a file' % path)

    def get_folder(self, path):
        f = self.get(path)
        if isinstance(f, GitFolder):
            return f
        else:
            raise NotADirectoryError('%s is not a folder' % path)

    def for_each_file(self, lamb):
        for fname in self.children():
            self._children[fname].for_each_file(lamb)
