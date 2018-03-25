import re

import gitcovery
from gitcovery import Git


class Author(object):
    """
    A commit author.
    Stores the name and email of the author alongside with all the commits that are known to be of this author.

    This class also keeps a static cache of all the authors in the repository.
    """
    _authors = {}
    _AUTHOR_REGEX = re.compile('(?P<name>.+)\n(?P<email>.+)\n(?P<commit>.+)\n' +
                               '(?P<commit_email>.+)\n(?P<sha>[a-f0-9]+)\n\n')

    def __init__(self, name, email):
        """
        Constructor for the author object from a name and email.

        :type name: str
        :param name: The name of the author
        :type email: str
        :param email: The email of the author
        """
        self.name = name
        self.emails = [email]
        self.commits = []

    def register_commit(self, commit):
        """
        Register a commit to this author.

        :type commit: Commit
        :param commit: The commit to register
        :rtype: bool
        :return: True when registration was successful, False otherwise
        """
        if commit not in self.commits:
            self.commits.append(commit)
            return True
        else:
            return False

    def register_email(self, email):
        """
        Register a email address to this author.

        :type email: str
        :param email: The commit to register
        :rtype: bool
        :return: True when registration was successful, False otherwise
        """
        if email not in self.emails:
            self.emails.append(email)
            return True
        else:
            return False

    @classmethod
    def _load_authors(cls):
        """
        Load all the authors of the repository.
        Adds all the email-addresses and associated commits.
        """
        if cls._authors:
            return
        out = Git.call(['log', '--format=%aN%n%aE%n%cN%n%cE%n%H%n'])

        def register(name, email):
            if name not in cls._authors:
                cls._authors[name] = Author(name, email)
            else:
                cls._authors[name].register_email(email)
            cls._authors[name].register_commit(gitcovery.Commit.get_commit(match.group('sha')))

        for match in cls._AUTHOR_REGEX.finditer(out):
            register(match.group('name'), match.group('email'))
            register(match.group('commit'), match.group('commit_email'))

    @classmethod
    def list(cls):
        """
        Get a list of all authors from the repository.

        :rtype: List[Author]
        :return: A list of all authors
        """
        cls._load_authors()
        return cls._authors.values()

    @classmethod
    def get_author(cls, name, email=''):
        """
        Get the Author object of the author with the given name.
        The email address is not necessary when searching and is appended to a known author.

        :type name: str
        :param name: The name of the author
        :type email: str
        :param email: (str) The email of the author (this value is optional)
        :rtype: Author
        :return: The requested Author object
        :raise Exception: When the author does not exist
        """
        name = name.strip()
        cls._load_authors()

        if name not in cls._authors:
            raise Exception(
                'Author <%s> not known' % name)

        if email:
            author = cls._authors[name]
            if email not in author.emails:
                author.register_email(email)
            return author

        else:
            return cls._authors[name]
