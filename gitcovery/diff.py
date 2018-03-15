import re


class _Diffable(object):
    """
    Interface implementing diffable behaviour.
    This means that you can get the number of added/removed/changed lines.
    """

    def num_added(self):
        """
        Get the number of added lines in this diff.

        :rtype: int
        :return: The number of added lines
        """
        raise Exception('Not implemented')

    def num_removed(self):
        """
        Get the number of removed lines in this diff.

        :rtype: int
        :return: The number of removed lines
        """
        raise Exception('Not implemented')

    def __len__(self):
        """
        Get the number of changed lines in this diff.

        :rtype: int
        :return: The number of changed lines in this diff
        """
        raise Exception('Not implemented')


class _DiffContainer(_Diffable):
    """
    A Diff containing object stores a list of Diffables.
    Implements all inherited functions by recursively calling
    them on the contained elements and accumulating the results.
    """

    def __init__(self, diffs):
        """
        Constructor for DiffContainer.
        Stores the given Siff objects it contains

        :type diffs: List[_Diffable]
        :param diffs: The contained diffs
        """
        self._diffs = diffs

    def __len__(self):
        total = 0
        for d in self._diffs:
            total += len(d)
        return total

    def num_added(self):
        total = 0
        for d in self._diffs:
            total += d.num_added()
        return total

    def num_removed(self):
        total = 0
        for d in self._diffs:
            total += d.num_removed()
        return total


class BlobDiff(object):
    """
    Class representing a code blob in the diff of a file.
    """

    def __init__(self, nums, lines):
        """
        Parses the contents of the git diff section describing a single blob of the diff.
        :type nums: str
        :param nums: The line numbers for this blob
        :type lines: str
        :param lines: The lines contained in the blob
        """
        # TODO: Store the actual diff data somehow
        self.added = []
        self.removed = []

        for line in lines.split('\n'):
            if line.startswith('+'):
                self.added.append(line)
            if line.startswith('-'):
                self.removed.append(line)

    def __len__(self):
        # TODO: This counts duplicates
        # some.code(here)
        # + a.foo()
        # - a.bar()
        # Should give 1 line change, but gives 2 with this implementation.
        return len(self.added) + len(self.removed)

    def num_added(self):
        return len(self.added)

    def num_removed(self):
        return len(self.removed)


class FileDiff(_DiffContainer):
    """
    A diff for a file. This diff contains one or more diff blobs.
    """

    # A regex to match and parse a blob in the diff
    _REGEX_FILEDIFF = re.compile('@@ (?P<nums>-[0-9]+,[0-9]+ \+[0-9]+,[0-9]+) @@\s(?P<diff>.*\n([\s+-].*\n*)*)')

    def __init__(self, fname, diff):
        """
        Constructs a FileDiff from a diff string.

        :type fname: str
        :param fname: The name of the file this diff belongs to.
        :type diff: str
        :param diff: The raw diff string to parse
        """
        super(FileDiff, self).__init__([])
        self.name = fname

        # For each blob in the diff
        match_iter = self._REGEX_FILEDIFF.finditer(diff)
        for match in match_iter:
            self._diffs.append(BlobDiff(match.group('nums'), match.group('diff')))


class Diff(_DiffContainer):
    """
    The diff of an entire commit. This diff consists of multiple FileDiffs.
    """

    # Regex that matches the contents of a file diff
    _REGEX_DIFF = re.compile('diff --git a/(?P<fname>.*) b/(?P=fname)' +
                             '(\nnew file mode .*)*\nindex.*\n--- (a/(?P=fname)|/dev/null)\n\+\+\+ b/(?P=fname)\n' +
                             '(?P<diff>@@.*@@(.*\n*)*?(?=\s*((diff --git)|\Z)))')

    def __init__(self, diffstr):
        """
        Constructor that builds the diff from the raw diff string.

        :type diffstr: str
        :param diffstr: The raw diff string to parse
        """
        super(Diff, self).__init__([])
        self.data = {}
        if not diffstr:     # Empty diff, do not parse
            return
        match_iter = self._REGEX_DIFF.finditer(diffstr)
        for matcher in match_iter:
            diff = FileDiff(matcher.group('fname'), matcher.group('diff'))
            self.add(diff)

    def add(self, file_diff):
        """
        Add a file diff to this diff.

        :type file_diff: FileDiff
        :param file_diff: The file diff to add
        """
        if file_diff.name in self.data:
            raise Exception('Diff already present for ' + file_diff.name)
        self.data[file_diff.name] = file_diff
        self._diffs.append(file_diff)

    def get_file(self, fname):
        """
        Get the FileDiff of the file with the given name.

        :type fname: str
        :param fname: The filename to get the diff for
        :rtype: FileDiff
        :return: The FileDiff for the given file
        """
        return self.data[fname]
