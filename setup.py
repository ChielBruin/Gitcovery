from setuptools import setup

setup(name='gitcovery',
      version='0.2',
      description='A wrapper for the git filesystem',
      url='http://github.com/ChielBruin/gitcovery',
      author='Chiel Bruin',
      author_email='github@bruin.ch',
      license='',
      packages=['gitcovery'],
      install_requires=[
          'python-dateutil'
      ],
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=[
            'nose',
            'parameterized',
            'python-dateutil'
      ],
      )
