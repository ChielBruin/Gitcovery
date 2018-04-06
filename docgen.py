import os
import re
import warnings


class FieldDef(object):
    """
    A field descriptor
    Stores the name type and documentation of a field.
    """

    # Regex to match static fields in a class body
    STATIC_REGEX = re.compile('((?P<docs>(\s{4}# .*\n)+)\s{4})?(?P<name>\w+)\s?=\s?.*# (?P<arg_desc>:type:\s*.*)\n')
    # Regex to find fields in the constructor
    REGEX_INIT = re.compile('((?P<docs>(\s{8}# .*\n)*)\s{8})?self.(?P<name>\w+)\s?=\s?.*# (?P<arg_desc>:type:\s*.*)\n')
    # Regex to parse field annotations (`return` is for properties)
    _REGEX_ANNOTATION = re.compile('(:r?type:\s*(?P<type>.*)\n?)(\s*:return:\s*(?P<desc>(.*\n*)*)\n?)?')

    def __init__(self, matcher, static):
        """
        Constructor for FieldDef.
        Builds the field definition from the given matched string.

        :type matcher: re.MatchObject
        :param matcher: The matcher to build from
        :type static: bool
        :param static: Whether this field is static or not
        """
        self.docs = matcher.group('docs') if matcher.group('docs') else ''
        self.docs = '\n'.join(map(lambda x: x.strip()[2:], self.docs.split('\n')))
        self.name = matcher.group('name')
        self.type = self.parse_arg_description(matcher.group('arg_desc'))
        self.static = static

    def parse_arg_description(self, annotation_str):
        """
        Parse the given string to a field description.

        :type annotation_str: str
        :param annotation_str: The string to parse
        :rtype: str
        :return: The parsing result
        """
        matcher = self._REGEX_ANNOTATION.search(annotation_str)

        # Void functions without arguments do never match
        if not matcher:
            return ''

        # The matcher has a description when it is a property. Therefore the docs must be set.
        if matcher.group('desc'):
            self.docs = matcher.group('desc')
        return matcher.group('type').strip()

    def __str__(self):
        """
        Convert the FieldDef into a markdown string

        :rtype: str
        :return: The string representation
        """
        static = ' - _static_' if self.static else ''
        return('**%s (%s)%s**\n\n%s' % (self.name, self.type, static, self.docs)).replace('[', '\[').replace(']', '\]')


class FunctionDef(object):
    """
    A function descriptor.
    Stores the parameters, signature, documentation and returned values.
    When the function overrides another function, this is also considered.
    """

    # Regex for matching function definitions
    REGEX = re.compile('(@(?P<annotation>\w*)\s*\n\s{4})?'
                       'def (?P<name>\w+)\s?\((?P<arguments>\w*(,\s\w+)*(?=[,)]))(,\s)?'
                       '(?P<optional_arguments>\w+=\w+(,\s\w)*)?\):\n\s{8}"""\n(?P<docs>(\s{8}.*\n)*?)'
                       '(?P<arg_desc>\n?\s{8}:.*\n(\s{8}.*\n)*?)?\s{8}"""\n(?P<body>(\s{8}.*\n)*)')
    # Regex to match argument descriptions in the docs
    _ARG_DESCRIPTION_REGEX = re.compile('\s*:((((type)|(?P<raises>raise))\s(?P<name>\w+))|(rtype)|):\s*(?P<type>(.*))'
                                        '(\n\s*:((param\s(?P=name))|(return)):\s*(?P<desc>.*))?')

    def __init__(self, matcher, parent):
        """
        Constructor for FunctionDef.
        Builds the function from the given matcher and parent class.

        :type matcher: re.MatchObject
        :param matcher: The matcher to build from
        :type parent: ClassDef
        :param parent: The parent class of the class where this function belongs to
        """
        self.name = matcher.group('name')

        arguments = matcher.group('arguments')
        arguments = arguments.replace('self', '').replace('cls', '')
        self.arguments = arguments[2:] if arguments.startswith(', ') else arguments

        self.optional_arguments = matcher.group('optional_arguments') if matcher.group('optional_arguments') else ''
        self._docs = matcher.group('docs')
        self._arg_desc = self.parse_argument_descriptors(matcher.group('arg_desc'))
        self.annotation = matcher.group('annotation')
        self.parent = parent

    @property
    def docs(self):
        """
        Builds the docs for this function and extends them by any possible overridden parent function.

        :rtype: str
        :return: The docs of this function
        """
        self_docs = '\n'.join(map(lambda x: x.strip(), self._docs.split('\n'))) if self._docs else ''
        if self.parent and self.name in self.parent.functions:
            return self.parent.functions[self.name].docs + '\n' + self_docs
        else:
            return self_docs

    @property
    def arg_desc(self):
        """
        Builds the argument descriptions for this function.
        When no descriptions are found, those of the parent function are returned.

        :rtype: str
        :return: The argument descriptions
        """
        if self._arg_desc:
            res = []
            for name, typ, desc in self._arg_desc:
                desc_str = '  \n  %s' % '\n'.join(map(lambda x: '  ' + x.strip(), desc.split('\n')))
                res.append('- **`%s`: %s**' % (name, typ) + desc_str)
            return '\n'.join(res)
        elif self.parent and self.name in self.parent.functions:
            return self.parent.functions[self.name].arg_desc
        else:
            num_args = len(self.arguments.split(', ')) if self.arguments else 0
            num_optional_args = len(self.optional_arguments.split(', ')) if self.optional_arguments else 0
            if num_args + num_optional_args > 0:
                warnings.warn('No argument documentation for %s()' % self.name)
            return ''

    def __str__(self):
        """
        Convert the FunctionDef into a markdown string

        :rtype: str
        :return: The string representation
        """
        annotation = ' - _static_' if (self.annotation == 'classmethod' or self.annotation == 'staticmethod') else ''
        if self.optional_arguments:
            if self.arguments:
                signature = '%s(%s, %s)' % (self.name, self.arguments, self.optional_arguments)
            else:
                signature = '%s(%s)' % (self.name, self.optional_arguments)
        else:
            signature = '%s(%s)' % (self.name, self.arguments)
        signature = signature.replace('_', '\\_')
        docs = self.docs

        return ('**%s%s**  \n%s%s' % (signature, annotation, docs, self.arg_desc)).replace('[', '\[').replace(']', '\]')

    @classmethod
    def parse_argument_descriptors(cls, raw):
        """
        Parses the arguments, return values and raised exceptions from the docs.

        :type raw: str
        :param raw:
        :rtype: List[(str, str, str)]
        :return: A list with the name, type and description of all arguments
        """
        res = []

        # Void function without arguments
        if not raw:
            return ''

        for desc_matcher in cls._ARG_DESCRIPTION_REGEX.finditer(raw):
            if desc_matcher.group('name'):
                if desc_matcher.group('raises'):
                    res.append(('Raises', desc_matcher.group('name'), desc_matcher.group('type')))
                else:
                    res.append((desc_matcher.group('name'), desc_matcher.group('type'), desc_matcher.group('desc')))
            else:
                res.append(('Returns', desc_matcher.group('type'), desc_matcher.group('desc')))
        return res


class ClassDef(object):
    """
    A class descriptor.
    Stores the fields, functions and class documentation.
    """

    # Regex that matches class definitions
    REGEX = re.compile('class (?P<name>_?[a-zA-Z]+)\s?\((?P<parent>_?[a-zA-Z]+)\):\n'
                       '\s*"""\n(?P<docs>(.*\n)+?)\s*"""\n*(?P<body>(.*\n)+?(?=(\n\n)|$))')

    def __init__(self, matcher):
        """
        Constructor for ClassDef.
        Builds the class from the given matcher.

        :type matcher: re.MatchObject
        :param matcher: The matcher to build from
        """
        self._fields = {}
        self._functions = {}
        self.name = matcher.group('name')
        self.parent = None if matcher.group('parent') == 'object' else Module.classes[matcher.group('parent')]
        self._docs = '\n'.join(map(lambda x: x.strip(), matcher.group('docs').split('\n')))

        # Match static fields
        for field_matcher in FieldDef.STATIC_REGEX.finditer(matcher.group('body')):
            name = field_matcher.group('name')
            if not name.startswith('_'):
                self._fields[name] = FieldDef(field_matcher, static=True)

        # Match functions
        for function_matcher in FunctionDef.REGEX.finditer(matcher.group('body')):
            name = function_matcher.group('name')

            # Get the fields from the constructor
            if name == '__init__':
                self.parse_fields(function_matcher.group('body'))
            if not name.startswith('_') or (name.startswith('__') and not name == '__init__'):
                if function_matcher.group('annotation') == 'property':
                    self._fields[name] = FieldDef(function_matcher, static=False)
                else:
                    self._functions[name] = FunctionDef(function_matcher, self.parent)

    @property
    def docs(self):
        """
        Builds the docs for this class and extends them by those of a parent class.

        :rtype: str
        :return: The docs of this class
        """
        if False and self.parent:
            return self._docs + '\n' + self.parent.docs
        else:
            return self._docs

    @property
    def functions(self):
        """
        Get a list of all functions in this class.
        Functions from its parent are also included.

        :rtype: Dict[str, FunctionDef]
        :return: A dictionary containing all functions by name
        """
        result = {}
        for func in self._functions:
            result[func] = self._functions[func]
        if self.parent:
            for func in self.parent.functions:
                if func not in self._functions:
                    result[func] = self.parent.functions[func]
        return result

    @property
    def fields(self):
        """
        Get a list of all fields in this class.
        Fileds from its parent are also included.

        :rtype: Dict[str, FieldDef]
        :return: A dictionary containing all fields by name
        """
        result = {}
        for field in self._fields:
            result[field] = self._fields[field]
        if self.parent:
            for field in self.parent.fields:
                if field not in self._fields:
                    result[field] = self.parent.fields[field]
        return result

    def __str__(self):
        """
        Convert the ClassDef into a markdown string

        :rtype: str
        :return: The string representation
        """
        header = '### %s' % self.name
        docs = self.docs

        field_str = '\n\n'.join(map(lambda x: str(x[1]), sorted(self.fields.items()))) + '\n' if self.fields else ''
        fun_str = '\n\n'.join(map(lambda x: str(x[1]), sorted(self.functions.items()))) + '\n' if self.functions else ''
        res = '%s\n\n%s\n\n' % (header, docs)
        if field_str:
            res += '#### Fields\n%s\n\n' % field_str
        if fun_str:
            res += '#### Functions\n%s' % fun_str
        return res

    def parse_fields(self, init_body):
        """
        Parse the fields from the body of the constructor.

        :type init_body: str
        :param init_body: The body of the constructor
        """
        for field_matcher in FieldDef.REGEX_INIT.finditer(init_body):
            name = field_matcher.group('name')
            if not name.startswith('_'):
                self._fields[name] = FieldDef(field_matcher, static=False)


class Module(object):
    """
    A Python module.
    Stores a list of classes, a description and a version number
    """
    _dir = ''
    _version = ''
    _description = ''
    classes = {}

    @classmethod
    def load_classes(cls):
        """
        Get the classes contained in this module as found in `__init__.py`

        :rtype: Dict[str, ClassDef]
        :return: The classes by name in a dictionary
        """
        if not cls.classes:
            with open(cls._dir + os.sep + '__init__.py') as init_file:
                regex = re.compile('from .(?P<name>[a-zA-z]+) import\s(?P<classes>(\w+(, )?)+)')
                classes = []
                for line in init_file.readlines():
                    if line.startswith('from'):
                        matcher = regex.match(line)
                        classes.extend(matcher.group('classes').split(', '))
                        file = matcher.group('name')
                        cls.read_classes_from_file(cls._dir + os.sep + file + '.py')
                        continue

                discovered = list(filter(lambda x: not x.startswith('_'), cls.classes.keys()))
                if sorted(classes) != sorted(discovered):
                    warnings.warn('Not all public classes are exposed in the module!\n'
                                  'Exposed: %r\nDiscovered: %r' % (classes, discovered))
        return cls.classes

    @classmethod
    def description(cls):
        """
        Get the description of the module as found in `__init__.py`.

        :rtype:
        :return:
        """
        if not cls._description:
            res = []
            with open(cls._dir + os.sep + '__init__.py') as init_file:
                in_doc = False
                for line in init_file.readlines():
                    if line.startswith('from'):
                        continue
                    if not line and not in_doc:
                        continue
                    if '"""' in line:
                        if not in_doc:
                            title = line.replace('"""', '').strip()
                            if title:
                                res.append('## %s\n' % title)
                        in_doc = not in_doc
                        continue
                    res.append(line)
            cls._description = ''.join(res)
        return cls._description

    @classmethod
    def read_classes_from_file(cls, file):
        """
        Read all the classes from the given files.

        :type file: str
        :param file: The file to read from
        """
        with open(file) as fh:
            for class_matcher in ClassDef.REGEX.finditer(fh.read()):
                cls.classes[class_matcher.group('name')] = ClassDef(class_matcher)

    @classmethod
    def set_dir(cls, location):
        """
        Set the home directory of the module.

        :type location: str
        :param location: The location of the module
        """
        cls._dir = location

    @classmethod
    def version(cls):
        """
        Get the version of the module.

        :rtype: str
        :return: The version of the module
        """
        if not cls._version:
            with open(cls._dir + os.sep + '..' + os.sep + 'setup.py') as fh:
                cls._version = re.search('version=\'(?P<version>(\d+.?)+)\'', fh.read()).group('version')
        return cls._version


if __name__ == '__main__':
    Module.set_dir('gitcovery')
    Module.load_classes()

    # Write the references to file
    with open('REFERENCE.md', 'w') as reference_file:
        reference_file.write('# Gitcovery reference documentation\n')
        reference_file.write('**\[Generated for gitcovery version %s\]**\n\n' % Module.version())
        reference_file.write(Module.description())
        reference_file.write('## Class overview\n\n')

        for class_name in sorted(Module.classes.keys()):
            if class_name.startswith('_'):
                continue
            reference_file.write(str(Module.classes[class_name]))
            reference_file.write('\n')
