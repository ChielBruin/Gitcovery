class Author(object):
    """
    A commit author.
    Stores the name and email of the author alongside with all the commits that are known to be of this author.
    """

    def __init__(self, name, email):
        """
        Constructor for the author object from a name and email.

        :type name: str
        :param name: The name of the author
        :type email: str
        :param email: The email of the author
        """
        self.name = name
        self.email = email
        self.commits = {}

    def register_commit(self, commit):
        """
        Register a commit to this author.

        :type commit: Commit
        :param commit: The commit to register
        :rtype: bool
        :return: True when registration was successful, False otherwise
        """
        if commit.sha not in self.commits:
            self.commits[commit.sha] = commit.sha
            return True
        else:
            return False
