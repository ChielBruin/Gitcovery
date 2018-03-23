from unittest import TestCase

from gitcovery import Git, GitFolder


class GitTest(TestCase):
    _patcher = None

    @classmethod
    def setUpClass(cls):
        """
        Setup for the tests. Clone the repo and set the correct version.
        """
        Git.clone('test-clone/', 'https://github.com/ChielBruin/Gitcovery.git')
        cls.root = Git.checkout('ede9c381daf318a87a58ed9607549132e150f145')

    def setUp(self):
        """
        Reset all the fields of Git.
        """
        Git._commits = {}
        Git._authors = {}
        Git._tags = None
        Git._initialCommits = []
        Git._head = None
        Git.root = ''

    def test_verify_root(self):
        """
        Make sure that verify root only throws an exception when the root is not set.
        """
        with self.assertRaises(Exception):
            Git._verify_root()
        Git.root = 'path/to/root'
        Git._verify_root()

    def test_set_root_not_exists(self):
        """
        Test the behaviour of set_root(), when the given root does not exist.
        """
        with self.assertRaisesRegexp(Exception, 'The file .* does not exist'):
            Git.set_root('/non/existent')

    def test_set_root_not_repository(self):
        """
        Test the behaviour of set_root(), when the given root is not a git repository.
        """
        with self.assertRaisesRegexp(Exception, '.* is not a Git repository'):
            Git.set_root('/')

    def test_set_root_empty(self):
        """
        Test the behaviour of set_root(), when the given root is empty.
        """
        with self.assertRaisesRegexp(Exception, 'Using the current directory is only supported by .*'):
            Git.set_root('')

    def test_set_root_correct(self):
        """
        Test the behaviour of set_root(), when the given root is correct.
        """
        result = Git.set_root('.')
        self.assertTrue(type(result) is GitFolder)
        self.assertEqual('.', result.path)

    def test_set_decode_settings_defaults(self):
        """
        Test the default values for the decoder.
        """
        encoding, error_policy = Git.set_decode_settings()
        self.assertEqual('utf-8', encoding)
        self.assertEqual('strict', error_policy)

    def test_set_decode_settings_set_error_policy(self):
        """
        Check if setting the error policy works correctly.
        """
        encoding, error_policy = Git.set_decode_settings(decode_error_policy='abc')
        self.assertEqual('utf-8', encoding)
        self.assertEqual('abc', error_policy)
        self.assertEqual('abc', Git._decode_error_policy)

        # Reset
        encoding, error_policy = Git.set_decode_settings(decode_error_policy='strict')
        self.assertEqual('strict', error_policy)

    def test_set_decode_settings_set_encoding(self):
        """
        Check if setting the encoding works correctly.
        """
        encoding, error_policy = Git.set_decode_settings(char_encoding='abc')
        self.assertEqual('abc', encoding)
        self.assertEqual('abc', Git._char_encoding)
        self.assertEqual('strict', error_policy)

        # Reset
        encoding, error_policy = Git.set_decode_settings(char_encoding='utf-8')
        self.assertEqual('utf-8', encoding)