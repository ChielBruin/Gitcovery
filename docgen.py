import re, os


class FunctionDef(object):
    REGEX = re.compile('def (?P<name>\w+)\s?\((?P<arguments>\w*(,\s\w+)*(?=,|\)))(,\s)?'
                       '(?P<optional_arguments>\w+=\w+(,\s\w)*)?\):\n\s{8}"""(?P<docs>(\s{8}.*\n)+?\n)?'
                       '(?P<arg_desc>(\s{8}.*\n)+?)\s{8}"""')

    def __init__(self, matcher):
        self.name = matcher.group('name')

        arguments = matcher.group('arguments')
        arguments = arguments.replace('self', '').replace('cls', '')
        self.arguments = arguments[2:] if arguments.startswith(', ') else arguments

        self.optional_arguments = matcher.group('optional_arguments')
        self.docs = matcher.group('docs')
        self.arg_desc = self.parse_argument_descriptors(matcher.group('arg_desc'))

    def __str__(self):
        header = '#####'
        if self.optional_arguments:
            signature = '`%s(%s, %s)`' % (self.name, self.arguments, self.optional_arguments)
        else:
            signature = '`%s(%s)`' % (self.name, self.arguments)
        docs = '\n'.join(map(lambda x: x.strip(), self.docs.split('\n'))) if self.docs else ''
        arg_desc = '\n'.join(map(lambda x: '- %s' % x, self.arg_desc))
        return ('%s %s\n%s%s' % (header, signature, docs, arg_desc)).replace('[', '\[').replace(']', '\]')

    @staticmethod
    def parse_argument_descriptors(raw):
        res = []
        for line in raw.split('\n'):
            line = line.strip()
            if line:
                res.append(line)
        return res


class ClassDef(object):
    REGEX = re.compile('class (?P<name>_?[a-zA-Z]+)\s?\((?P<parent>_?[a-zA-Z]+)\):\n'
                       '\s*"""\n(?P<docs>(.*\n)+?)\s*"""\n*(?P<body>(.*\n)+?(?=(\n\n)|$))')

    def __init__(self, matcher):
        self.functions = {}
        self.name = matcher.group('name')
        self.parent = None if matcher.group('parent') == 'object' else matcher.group('parent')
        self.docs = '\n'.join(map(lambda x: x.strip(), matcher.group('docs').split('\n')))

        for function_matcher in FunctionDef.REGEX.finditer(matcher.group('body')):
            name = function_matcher.group('name')
            if not name.startswith('_') or (name.startswith('__') and not name == '__init__'):
                self.functions[name] = FunctionDef(function_matcher)

    def __str__(self):
        header = '### %s' % self.name
        docs = self.docs

        def str_functions(functions):
            res = []
            for function_name in sorted(functions.keys()):
                res.append(str(functions[function_name]))
            return '\n\n'.join(res) + '\n'

        if self.parent:
            parent_functions = str_functions(Module.classes[self.parent].functions)
        else:
            parent_functions = ''
        self_functions = str_functions(self.functions)
        return '%s\n\n%s\n\n%s%s' % (header, docs, parent_functions, self_functions)


class Module(object):
    _dir = ''
    _version = ''
    classes = {}

    @classmethod
    def description(cls):
        res = []
        with open(cls._dir + os.sep + '__init__.py') as init_file:
            in_doc = False
            for line in init_file.readlines():
                if line.startswith('from'):
                    file = re.compile('from .(?P<name>[a-zA-z]+) import.*').match(line).group('name')
                    cls.read_file(cls._dir + os.sep + file + '.py')
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
        return ''.join(res)

    @classmethod
    def read_file(cls, file):
        with open(file) as fh:
            for class_matcher in ClassDef.REGEX.finditer(fh.read()):
                cls.classes[class_matcher.group('name')] = ClassDef(class_matcher)

    @classmethod
    def set_dir(cls, location):
        cls._dir = location

    @classmethod
    def version(cls):
        if not cls._version:
            with open(cls._dir + os.sep + '..' + os.sep + 'setup.py') as fh:
                cls._version = re.search('version=\'(?P<version>(\d+.?)+)\'', fh.read()).group('version')
        return cls._version


if __name__ == '__main__':
    Module.set_dir('gitcovery')
    with open('REFERENCE.md', 'w') as reference_file:
        reference_file.write('# Gitcovery reference documentation\n')
        reference_file.write('**\[Generated for gitcovery version %s\]**\n\n' % Module.version())
        reference_file.write('> ### This reference file is currently in BETA\n')
        reference_file.write('> Therefore, there are a few known issues and future improvements:\n')
        reference_file.write('> - Public fields are not shown\n')
        reference_file.write('> - Inherited functions do not show correctly (or at all)\n')
        reference_file.write('> - Inherited docs are not shown\n')
        reference_file.write('> - Argument descriptors are not formatted\n\n')
        reference_file.write(Module.description())
        reference_file.write('## Class overview\n\n')

        for class_name in sorted(Module.classes.keys()):
            if class_name.startswith('_'):
                continue
            reference_file.write(str(Module.classes[class_name]))
            reference_file.write('\n')
