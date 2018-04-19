import re
import warnings
from dateutil import parser as dp

from gitcovery import Author
from .git import Git
from .diff import Diff


class Commit(object):
    """
    Class representing a commit.
    A commit stores all the relevant data on a commit like the author,
    the date of the commit, the commit message and the diff.
    """

    _REGEX_COMMIT = re.compile('(?P<sha>([a-f0-9]+)\n)?(?P<parents>([a-f0-9]+\s?)*)\n' +
                               '(?P<author>.+)\n(?P<authorMail>.+)\n(?P<authorDate>[0-9\-:\s+]+)\n' +
                               '(?P<commit>.+)\n(?P<commitMail>.+)\n(?P<commitDate>[0-9\-:\s+]+)\n' +
                               '(?P<title>.*)(?P<message>(.*\n)*?(?=(diff --git)|\Z|([0-9a-f]+\n)))?' +
                               '(?P<diff>diff (.*\n)*?(?=([a-f0-9]+\n)|\Z))?')
    _commits = {}  # :type: Dict[str, Commit]

    def __init__(self, sha, preload=False):
        """
        Construct a Commit instance for a given commit SHA hash.
        By default the other data is only loaded when it is needed.
        This is due to performance reasons, as querying git is relatively slow.

        :type sha: str
        :param sha: The SHA has of the commit
        :type preload: bool
        :param preload: Whether to load all the data directly, False by default
        """
        # The SHA hash of the commit.
        self.sha = sha         # :type: str
        self._author = None
        self._authorDate = ''
        self._commit = None
        self._commitDate = ''
        self._title = ''
        self._msg = ''
        self._diff = None
        self._parents = []

        if preload:
            self.load()

    def _set_from_string(self, matcher, load_diff=True):
        """
        Set the contents of this commit with the data from the given matcher.

        :type matcher: matcher
        :param matcher: The used to load
        :type load_diff: bool
        :param load_diff: Whether to load the diff from the string
        """

        if not matcher:
            raise Exception(
                'git show output could not be matched for: %s\n' % self.sha +
                'Please report the commit hash and repository so I can improve the regex')

        try:
            # Parse parents
            for sha in matcher.group('parents').split(' '):
                if sha == '':
                    continue
                self._parents.append(self.get_commit(sha))

            # Parse authors
            self._author = Author.get_author(matcher.group('author'), email=matcher.group('authorMail'))
            self._commit = Author.get_author(matcher.group('commit'), email=matcher.group('commitMail'))

            self._author.register_commit(self)

            self._authorDate = dp.parse(matcher.group('authorDate'))
            self._commitDate = dp.parse(matcher.group('commitDate'))

            # Parse the commit contents
            self._title = matcher.group('title')
            self._msg = matcher.group('message').strip() if matcher.group('message') else ''

            # Parse the diff if provided
            if load_diff:
                self._diff = Diff(matcher.group('diff'))
            else:
                self._diff = None
        except Exception as e:
            raise Exception('Cannot construct commit %s from the given output' % self.sha +
                            'Please report the commit hash and repository so I can fix the problem', e)

    def _load_diff(self):
        """
        Load only the diff data for this commit.
        """
        if self._diff:
            return
        self._diff = Diff(Git.call(['show', '--pretty=format:', self.sha]))

    def load(self):
        """
        Load the data for this commit.
        This function calls 'git show' and parses the output.

        :rtype: bool
        :return: True when successfully loaded, False when already loaded
        """
        # If already loaded, skip
        if self._author:
            return False

        out = Git.call(['show', '--pretty=format:%P%n%aN%n%aE%n%ai%n%cN%n%cE%n%ci%n%s%n%b', self.sha])
        self._set_from_string(self._REGEX_COMMIT.search(out))
        return True

    def unload(self):
        """
        Unload all the cached data for this commit.
        """
        self._author = None
        self._authorDate = ''
        self._commit = None
        self._commitDate = ''
        self._title = ''
        self._msg = ''
        self._diff = None
        self._parents = []

    @property
    def author(self):
        """
        :rtype: Author
        :return: The author of this commit
        """
        self.load()
        return self._author

    @property
    def author_date(self):
        """
        :rtype: datetime.datetime
        :return: The author date
        """
        self.load()
        return self._authorDate

    @property
    def commit(self):
        """
        :rtype: Author
        :return: The commit author of this commit
        """
        self.load()
        return self._commit

    @property
    def commit_date(self):
        """
        :rtype: datetime.datetime
        :return: The commit author date
        """
        self.load()
        return self._commitDate

    @property
    def title(self):
        """
        :rtype: str
        :return: The commit title
        """
        self.load()
        return self._title

    @property
    def message(self):
        """
        :rtype: str
        :return: The commit message
        """
        self.load()
        return self._msg

    @property
    def parents(self):
        """
        :rtype: List[Commit]
        :return: A list of the parents of this commit
        """
        self.load()
        return self._parents

    def changes(self, file_name=None):
        """
        Get the diff for this commit.
        When file_name is given, only the diff for that file is returned.

        :type file_name: str
        :param file_name: Optional file name to get the diff from
        :rtype: _DiffContainer
        :return: The diff of this commit
        """
        if not self._diff and not self.load():
            self._load_diff()
        if file_name:
            return self._diff.get_file(file_name)
        else:
            return self._diff

    def __lt__(self, other):
        """
        Compare this commit with another based on the date of the commit.

        :type other: Commit
        :param other: The object to compare to
        :rtype: bool
        :return: True when this commit is older than the given commit, False otherwise
        """
        if not isinstance(other, Commit):
            raise TypeError

        self.load()

        return self.author_date < other.author_date

    def __eq__(self, other):
        """
        Two Commits are equal when their hashes match.

        :type other: object
        :param other: The object to compare with
        :rtype: bool
        :return: True when they are equal, False otherwise
        """
        if isinstance(other, Commit):
            return self.sha == other.sha
        return False

    def for_each_parent(self, func):
        """
        Execute a function for this commit and all its parents (AKA the tree that this commit is part of).

        :type func: Commit -> None
        :param func: The function to apply for each parent recursively
        """
        func(self)

        for child in self.parents():
            child.forEachChild(func)

    @classmethod
    def get_commit(cls, sha):
        """
        Get a commit with the given hash from the cache.
        When it is not present in the cache, a new commit is created.

        :type sha: str
        :param sha: The SHA hash of the commit to get
        :rtype: Commit
        :return: The requested Commit object
        :raise: Exception, when the given hash is empty
        """
        if not sha:
            raise Exception('Invalid sha \'%s\'' % sha)
        if sha in cls._commits:
            return cls._commits[sha]
        else:
            commit = Commit(sha)
            cls._commits[sha] = commit
            return commit

    @classmethod
    def load_all(cls, load_diff=False):
        """
        Preload all the metadata of all commits.
        This method should be used when loading a large number of commits,
        as a significant speedup is achieved in this case.
        By default the meatadata does not include the diffs.
        This is done to reduce the execution time and most notably the memory usage.
        You can specify to load the diffs, but this is not recommended unless you need the diffs for all commits.

        :type load_diff: bool
        :param load_diff: Whether to load the diff data
        """
        if load_diff:
            warnings.warn('Loading all the diff data can take very much memory for large repositories '
                          '(Multiple GBs for > 20000 commits)')

            out = Git.call(['log', '-p', '--pretty=format:%H%n%P%n%aN%n%aE%n%ai%n%cN%n%cE%n%ci%n%s%n%b'])
        else:
            out = Git.call(['log', '--pretty=format:%H%n%P%n%aN%n%aE%n%ai%n%cN%n%cE%n%ci%n%s%n%b'])
        for matcher in cls._REGEX_COMMIT.finditer(out):
            cls.get_commit(matcher.group('sha').strip())._set_from_string(matcher, load_diff=load_diff)
