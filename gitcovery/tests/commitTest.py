import json
import unittest

from dateutil import parser as dp
from parameterized import parameterized

from gitcovery import Commit, Git


def load_params():
    """
    Load the parameters for the commit loading tests from file.

    :return: A list of tuples (sha, data) containing the test data
    """
    result = []
    with open('gitcovery/tests/resources/commit_test_data.json') as data_file:
        data = json.load(data_file)
        for sha in data:
            result.append((sha, data[sha]))
    return result


class CommitTest(unittest.TestCase):
    """
    Test class for Commit.
    """

    @classmethod
    def setUpClass(cls):
        """
        Setup for the tests. Clone the repo and set the correct version.
        """
        Git.clone('test-clone/', 'https://github.com/ChielBruin/Gitcovery.git')
        cls.root = Git.checkout('ede9c381daf318a87a58ed9607549132e150f145')

    def setUp(self):
        """
        Create a fresh instance for each test case.
        """
        self.instance = Commit('9b423f8c38516ed33acfa907ae56ad3868741803')

    @parameterized.expand(load_params())
    def test_parse_test(self, sha, data):
        """
        Test the loading of specific commits.

        :param sha: The commit to load
        :param data: The data to check against
        """
        self.instance = Commit(sha)
        self.instance.load()

        msg = 'Test failed for commit with sha %s' % sha

        self.assertEqual(data['author'], self.instance.author.name, msg)
        self.assertEqual(data['commit'], self.instance.commit.name, msg)

        self.assertEqual(dp.parse(data['authorDate']), self.instance.author_date, msg)
        self.assertEqual(dp.parse(data['commitDate']), self.instance.commit_date, msg)

        self.assertEqual(data['title'], self.instance.title, msg)
        self.assertEqual(data['msg'], self.instance.message, msg)

        self.assertEqual(data['parents'], list(map(lambda x: x.sha, self.instance.parents)), msg)

        self.assertEqual(data['numFiles'], len(self.instance.changes().data))

    def test_unload(self):
        """
        Test the unload function.
        First loads, checks if the data is there, unloads and checks if the data is gone.
        """
        self.instance.load()
        self.assertIsNotNone(self.instance._author)
        self.instance.unload()
        self.assertIsNone(self.instance._author)

    def test_lt_invalid(self):
        """
        Test that comparing a Commit to a number gives an error.
        """
        with self.assertRaises(TypeError):
            self.instance < 12

    def test_lt_self(self):
        """
        Test if you are older than yourself.
        """
        self.assertFalse(self.instance < self.instance)

    def test_lt_true(self):
        """
        Test if an older commit is less than the instance.
        """
        self.assertTrue(self.instance < Commit('ede9c381daf318a87a58ed9607549132e150f145'))

    def test_lt_false(self):
        """
        Test if a newer commit is not less then the instance.
        :return:
        """
        self.assertFalse(self.instance < Commit('f3ccd0b70fe758b539c28319735d9a6489c0fb10'))

    def test_eq_invalid(self):
        """
        Test if a Commit is not equal to a string.
        """
        self.assertFalse(self.instance == '123')

    def test_eq_true(self):
        """
        Test that you are equal when the hash is equal.
        """
        self.assertTrue(self.instance == Commit(self.instance.sha))

    def test_eq_false(self):
        """
        Test that you are not equal when the hashes differ.
        """
        self.assertFalse(self.instance == Commit('f3ccd0b70fe758b539c28319735d9a6489c0fb10'))