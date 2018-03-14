import re
from dateutil import parser as dp

from .git import Git
from .diff import Diff


class Commit(object):
    """
    Class representing a commit.
    A commit stores all the relevant data on a commit like the author,
    the date of the commit, the commit message and the diff.
    """

    # Regex to parse the 'git show' output
    _REGEX_COMMIT = re.compile('(?P<parents>([a-f0-9\s]+\s?)*)\n' +
                               '(?P<author>.+)\n(?P<authorMail>.+@.+)\n(?P<authorDate>[0-9\-]+ [0-9:]+ [+\-0-9]+)\n' +
                               '(?P<commit>.+)\n(?P<commitMail>.+@.+)\n(?P<commitDate>[0-9\-]+ [0-9:]+ [+\-0-9]+)\n' +
                               '(?P<title>.*)(?P<message>(.*\n)*)?\n(?P<diff>diff (.*\n)*)?')

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
        self.sha = sha
        self._author = None
        self._authorDate = ''
        self._commit = None
        self._commitDate = ''
        self._title = ''
        self._msg = ''
        self._diff = None
        self._parents = []
        self._children = []

        if preload:
            self.load()

    def load(self):
        """
        Load the data for this commit.
        This function calls 'git show' and parses the output.
        """
        # If already loaded, skip
        if self._author:
            return

        out = Git.call(['show', '--pretty=format:%P%n%an%n%ae%n%ai%n%cn%n%ce%n%ci%n%s%n%b', self.sha])
        matcher = self._REGEX_COMMIT.search(out)

        if not matcher:
            raise Exception(
                'git show output could not be matched: %s\n\n' % out +
                'If you are sure this should be matched, please report the output so I can improve the regex')

        # Parse parents
        for sha in matcher.group('parents').split(' '):
            if sha == '':
                continue
            commit = Git.get_commit(sha)
            self._parents.append(commit)
            commit.register_child(self)

        # Parse authors
        self._author = Git.get_author(matcher.group('author'), email=matcher.group('authorMail'))
        self._commit = Git.get_author(matcher.group('commit'), email=matcher.group('commitMail'))

        self._author.register_commit(self)

        self._authorDate = dp.parse(matcher.group('authorDate'))
        self._commitDate = dp.parse(matcher.group('commitDate'))

        # Parse the commit contents
        self._title = matcher.group('title')
        self._msg = matcher.group('message') if matcher.group('message') else ''
        self._diff = Diff(matcher.group('diff'))

    def author(self):
        """
        :rtype: Author
        :return: The author of this commit
        """
        self.load()
        return self._author

    def author_date(self):
        """
        :rtype: datetime.datetime
        :return: The author date
        """
        self.load()
        return self._authorDate

    def commit(self):
        """
        :rtype: Author
        :return: The commit author of this commit
        """
        self.load()
        return self._commit

    def commit_date(self):
        """
        :rtype: datetime.datetime
        :return: The commit author date
        """
        self.load()
        return self._commitDate

    def title(self):
        """
        :rtype: str
        :return: The commit title
        """
        self.load()
        return self._title

    def msg(self):
        """
        :rtype: str
        :return: The commit message
        """
        self.load()
        return self._msg

    def changes(self, file_name=None):
        """
        Get the diff for this commit.
        When file_name is given, only the diff for that file is returned.

        :type file_name: str
        :param file_name: Optional file name to get the diff from
        :rtype: _DiffContainer
        :return: The diff of this commit
        """
        self.load()
        if file_name:
            return self._diff.get_file(file_name)
        else:
            return self._diff

    def register_child(self, commit):
        """
        Register a child to this commit.

        :type commit: Commit
        :param commit: The commit to add as a child
        :rtype: bool
        :return: True when successful, False otherwise
        """
        if commit not in self._children:
            self._children.append(commit)
            return True
        else:
            return False

    def parents(self):
        """
        :rtype: List[Commit]
        :return: A list of the parents of this commit
        """
        self.load()
        return self._parents

    def children(self):
        """
        Get all the commits that registered themselves as children.
        Note: this list might not be complete, so please make sure all possible children are loaded.

        :rtype: List[Commit]
        :return: A list of all the currently known children of this commit
        """
        self.load()
        return self._children

    def __lt__(self, other):
        """
        Compare this commit with another based on the date of the commit.

        :type other: Commit
        :param other: The object to compare to
        :rtype: bool
        :return: True when this commit is older than the given commit, False otherwise
        """
        self.load()

        return self.author_date() < other.author_date()

    def for_each_parent(self, func):
        """
        Execute a function for this commit and all its parents (AKA the tree that this commit is part of).

        :type func: Commit -> None
        :param func: The function to apply for each parent recursively
        """
        func(self)

        for child in self.parents():
            child.forEachChild(func)
