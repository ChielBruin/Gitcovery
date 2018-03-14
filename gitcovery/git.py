import os
import re
import subprocess

import gitcovery


class Git(object):
    """
    Main class of this module. This class represents the interface to Git,
    where all other classes are data objects that represent data from Git.
    It exposes a number of static methods that allow you to select or clone
    the repository, do a checkout on a specific branch or make direct calls to Git.

    In addition to this, the Git class also contains a cache of all the commmits
    and authors, the tags in the repository and a reference to HEAD and the initial commit.
    """
    _commits = {}
    _authors = {}
    _tags = None
    _initialCommits = []
    _head = None
    root = ''

    # Regex for matching tags and their commit hashes
    _REGEX_TAGS = re.compile('(?P<commit>[0-9a-z]+) refs/tags/(?P<tag>.*)')

    @classmethod
    def _verify_root(cls):
        """
        Verify that the root is set, otherwise throws an exception.
        This does not validate the root, as this is already done while setting the root.

        :raise: Exception, when the root is not set
        """
        if not cls.root:
            raise Exception('Please set the git root first')

    @classmethod
    def clone(cls, loc, addr):
        """
        Clone a git repository to the specified location and return a reference to the root.
        When there is already a folder with the correct name at that location, cloning is skipped.
        Calling this function is identical to calling
        `cd loc && git clone addr` and setting the root to this location.

        :type loc: str
        :param loc: The location to clone to
        :type addr: str
        :param addr: The location of the repository to clone
        :rtype: GitFolder
        :return: A reference to the root
        """
        name = re.search('/(?P<name>[^/]+)\.git$', addr).group('name')
        if not os.path.isdir(loc + os.sep + name):
            cls.call(['clone', addr], root=loc)
        return cls.set_root(loc + os.sep + name)

    @classmethod
    def checkout(cls, name):
        """
        Checkout a specific branch in the repository.
        Calling this function is identical to calling `git checkout name` and setting the root again.
        Note that previously created GitFile and GitFolder instances might be broken.
        This is because files can be (re)moved on the new branch. It is therefore
        advised to use the returned root to reconstruct all references.

        :type name: str
        :param name: The name of the branch to checkout
        :rtype: GitFolder
        :return: A reference to the root
        """
        cls._verify_root()
        cls.call(['checkout', name])
        return gitcovery.GitFolder(cls.root)

    @classmethod
    def set_root(cls, root):
        """
        Set the root of the repository to the specified location.
        When not using the clone-function, this is the first thing you should call when using the module.
        Please note that if you want to set the root to the current directory,
        a . (period) is expected instead of the empty string.

        :type root: str
        :param root: The path to the root of the repository.
        :rtype: GitFolder
        :return: A reference to the root
        """
        if root == '':
            # Converting this to a . is easy, but it might not be what the user wants.
            # Therefore the error is thrown containing a possible solution.
            raise Exception('Using the current directory is only supported by setting the root to \'.\'')
        cls.root = root
        folder = gitcovery.GitFolder(root)

        # Check if the root is a git repository
        try:
            folder.status()
        except Exception:
            raise Exception('%s is not a Git repository' % root)

        return folder

    @classmethod
    def call(cls, cmds, root=None, kill_on_error=True):
        """
        Call the git subsystem via the command line and return the output.
        Kills the process when the call fails (unless specified otherwise).
        You are not encouraged to use this call directly, when you have a valid reason to do so
        you might want to consider to request a feature on GitHub.

        :type cmds: List[str]
        :param cmds: A list of arguments to pass to the command line.
            Note that 'git' is always prepended
        :type root: str
        :param root: When set uses a different working directory to run the command.
            When not specified the root of the repository is used.
        :type kill_on_error: bool
        :param kill_on_error: Indicates whether an error should kill the process (True by default)
        :rtype: str
        :return: The output of running the command
        """
        try:
            if not root:
                cls._verify_root()
                root = cls.root
            return subprocess.check_output(['git'] + cmds, stderr=subprocess.STDOUT, cwd=root).decode('utf-8')
        except subprocess.CalledProcessError as e:
            if kill_on_error:
                print(e.cmd, e.output.decode())
                exit(-1)
            else:
                raise ChildProcessError(e)

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
            commit = gitcovery.Commit(sha)
            cls._commits[sha] = commit
            return commit

    @classmethod
    def authors(cls):
        """
        Get a list of all authors from the cache.
        Because the authors are only cached when they are encountered,
        you need to make sure that every commit that could introduce a new author is loaded.

        :rtype: List[Author]
        :return: A list of all cached authors
        """
        return cls._authors.values()

    @classmethod
    def get_author(cls, name, email=''):
        """
        Get an Author object from the cache with a given name.
        When an author is not present, it is created and added to the cache (as long as an email is provided)
        The email address is not neccesary when searching, the name suffices.

        :type name: str
        :param name: The name of the author
        :type email: str
        :param email: (str) The email of the author (this value is optional)
        :rtype: Author
        :return: The requested Author object
        """
        name = name.strip()
        if name not in cls._authors:
            if email:
                cls._authors[name] = gitcovery.Author(name, email)
            else:
                raise Exception(
                    'Author <%s> not known, did you load all commits (as you are reading from cached values)?' % name)

        # TODO: Check the email and add it if email is unknown for that author
        return cls._authors[name]

    @classmethod
    def get_tags(cls):
        """
        Get a list of all the tags of this project.
        These tags can directly be passed to 'Git.getTag(tag)'

        :rtype: List[str]
        :return: A list of all tags, without ordering.
        """
        if cls._tags is None:
            cls._tags = {}
            out = cls.call(['show-ref', '--tags'], kill_on_error=False)  # A repo without tags gives an error
            matcher = cls._REGEX_TAGS.finditer(out)
            for match in matcher:
                cls._tags[match.group('tag')] = cls.get_commit(match.group('commit'))
        return list(cls._tags.keys())

    @classmethod
    def get_tags_by_commit(cls):
        """
        Get a list of all the tags and their commit in the following format:
        [(Commit, tag), ...], this list can be sorted in chronological order using the builtin sort

        :rtype: (List[(Commit, str)])
        :return: A list of all tags and commits.
        """
        if cls._tags is None:
            cls.get_tags()
        return list(map(lambda tag: (cls._tags[tag], tag), cls._tags.keys()))

    @classmethod
    def get_tag(cls, tag):
        """
        Get the Commit associated with the given tag.

        :type tag: str
        :param tag: The tag to get the Commit from
        :rtype: Commit
        :return The commit associated with the tag
        """
        if cls._tags is None:
            cls.get_tags()
        return cls._tags[tag]

    @classmethod
    def get_initial_commits(cls):
        """
        Get the initial commits of this repository.
        Note that it is possible to have multiple roots, therefore a list is returned.

        :rtype: List[Commit]
        :return: A list of initial commits
        """
        if not cls._initialCommits:
            out = cls.call(['rev-list', '--max-parents=0', 'HEAD'])
            cls._initialCommits = map(lambda x: cls.get_commit(x), out.split('\n')[0:-1])
        return cls._initialCommits

    @classmethod
    def get_head(cls):
        """
        Get the commit associated with HEAD.

        :rtype: Commit
        :return: The commit at HEAD
        """
        if not cls._head:
            out = cls.call(['rev-parse', 'HEAD'])
            cls._head = Git.get_commit(out.strip())
        return cls._head
