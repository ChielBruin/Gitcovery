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

    In addition to this, the Git class also contains a cache of all the commits
    and the tags in the repository and a reference to HEAD and the initial commit.
    """
    _decode_error_policy = 'strict'
    _char_encoding = 'utf-8'

    _tags = None
    _initialCommits = []
    _head = None
    root = None

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
    def clone(cls, loc, address, update=False):
        """
        Clone a git repository to the specified location and return a reference to the root.
        When there is already a folder with the correct name at that location, cloning is skipped.
        Calling this function is identical to calling
        `cd loc && git clone addr` and setting the root to this location.
        Optionally, you could update the repository (when it already exists) by setting `update` to True.

        :type update: bool
        :param update: whether to update the repository when already cloned
        :type loc: str
        :param loc: The location to clone to
        :type address: str
        :param address: The location of the repository to clone
        :rtype: GitFolder
        :return: A reference to the root
        """
        name = re.search('/(?P<name>[^/]+)\.git$', address).group('name')
        loc = loc[0:-1] if loc.endswith('/') else loc
        if not os.path.exists(loc):
            os.mkdir(loc)
        path = loc + os.sep + name
        if not os.path.isdir(path):
            cls.call(['clone', address], root=loc)
        elif update:
            cls.call(['pull'], root=path)
        return cls.set_root(path)

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
        return cls.set_root(cls.root.path)

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
        folder = gitcovery.GitFolder(root)
        cls.root = folder

        # Check if the root is a git repository
        try:
            folder.status()
        except IOError:
            raise Exception('%s is not a Git repository' % root)

        return folder

    @classmethod
    def set_decode_settings(cls, char_encoding=None, decode_error_policy=None):
        """
        Set the settings of the decoder for raw git output.
        See https://docs.python.org/2/library/codecs.html#codec-base-classes for valid error policies.

        :type char_encoding: str
        :param char_encoding: Optional, the encoding to use to decode the output
        :type decode_error_policy: str
        :param decode_error_policy: The policy to use when an error is encountered.
        :rtype: (str, str)
        :return: A tuple containing the new encoding and error policy
        """
        if char_encoding:
            cls._char_encoding = char_encoding
        if decode_error_policy:
            cls._decode_error_policy = decode_error_policy

        return cls._char_encoding, cls._decode_error_policy

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
        :raise IOError: When the command fails and kill_on_error==False
        """
        try:
            if not root:
                cls._verify_root()
                root = cls.root.path
            return subprocess.check_output(['git'] + cmds, stderr=subprocess.STDOUT, cwd=root).decode(cls._char_encoding, errors=cls._decode_error_policy)
        except subprocess.CalledProcessError as e:
            if kill_on_error:
                print(e.cmd, e.output.decode())
                exit(-1)
            else:
                raise IOError(e)

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
                cls._tags[match.group('tag')] = gitcovery.Commit.get_commit(match.group('commit'))
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
            cls._initialCommits = map(lambda x: gitcovery.Commit.get_commit(x), out.split('\n')[0:-1])
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
            cls._head = gitcovery.Commit.get_commit(out.strip())
        return cls._head
