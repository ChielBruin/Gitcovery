import re, os


class FieldDef(object):
    STATIC_REGEX = re.compile('((?P<docs>(\s{4}# .*\n)+)\s{4})?(?P<name>\w+)\s?=\s?.*# (?P<arg_desc>:type:\s*.*)\n')
    REGEX_INIT = re.compile('((?P<docs>(\s{8}# .*\n)*)\s{8})?self.(?P<name>\w+)\s?=\s?.*# (?P<arg_desc>:type:\s*.*)\n')
    _REGEX_ANNOTATION = re.compile('(:r?type:\s*(?P<type>.*)\n?)(\s*:return:\s*(?P<desc>(.*\n*)*)\n?)?')

    def __init__(self, matcher, parent, static):
        self._docs = matcher.group('docs') if matcher.group('docs') else ''
        self._docs = '\n'.join(map(lambda x: x.strip()[2:], self._docs.split('\n')))
        self.name = matcher.group('name')
        self._type = self.parse_arg_description(matcher.group('arg_desc'))
        self.static = static

    def parse_arg_description(self, annotation_str):
        matcher = self._REGEX_ANNOTATION.search(annotation_str)
        if matcher.group('desc'):
            self._docs = matcher.group('desc')
        return matcher.group('type').strip()

    @property
    def docs(self):
        return self._docs

    @property
    def type(self):
        return self._type

    def __str__(self):
        static = ' - _static_' if self.static else ''
        return('**%s (%s)%s**\n\n%s' % (self.name, self._type, static, self.docs)).replace('[', '\[').replace(']', '\]')


class FunctionDef(object):
    REGEX = re.compile('(@(?P<annotation>\w*)\s*\n\s{4})?'
                       'def (?P<name>\w+)\s?\((?P<arguments>\w*(,\s\w+)*(?=[,)]))(,\s)?'
                       '(?P<optional_arguments>\w+=\w+(,\s\w)*)?\):\n\s{8}"""(?P<docs>(\s{8}.*\n)+?\n)?'
                       '(?P<arg_desc>(\s{8}.*\n)+?)\s{8}"""\n(?P<body>(\s{8}.*\n)*)')
    _ARG_DESCRIPTION_REGEX = re.compile('\s*:((((type)|(?P<raises>raise))\s(?P<name>\w+))|(rtype)|):\s*(?P<type>(.*))'
                                        '(\n\s*:((param\s(?P=name))|(return)):\s*(?P<desc>.*))?')

    def __init__(self, matcher, parent):
        self.name = matcher.group('name')

        arguments = matcher.group('arguments')
        arguments = arguments.replace('self', '').replace('cls', '')
        self.arguments = arguments[2:] if arguments.startswith(', ') else arguments

        self.optional_arguments = matcher.group('optional_arguments')
        self._docs = matcher.group('docs')
        self._arg_desc = self.parse_argument_descriptors(matcher.group('arg_desc'))
        self.annotation = matcher.group('annotation')
        self.parent = parent

    @property
    def docs(self):
        self_docs = '\n'.join(map(lambda x: x.strip(), self._docs.split('\n'))) if self._docs else ''
        if self.parent and self.name in self.parent.functions:
            return self.parent.functions[self.name].docs + '\n' + self_docs
        else:
            return self_docs

    @property
    def arg_desc(self):
        if self._arg_desc:
            res = []
            for name, typ, desc in self._arg_desc:
                desc_str = '  \n  %s' % '\n'.join(map(lambda x : '  ' + x.strip(), desc.split('\n')))
                res.append('- **`%s`: %s**' % (name, typ) + desc_str)
            return '\n'.join(res)
        elif self.parent and self.name in self.parent.functions:
            return self.parent.functions[self.name].arg_desc
        else:
            return ''

    def __str__(self):
        annotation = ' - _static_' if (self.annotation == 'classmethod' or self.annotation == 'staticmethod') else ''
        if self.optional_arguments:
            signature = '%s(%s, %s)' % (self.name, self.arguments, self.optional_arguments)
        else:
            signature = '%s(%s)' % (self.name, self.arguments)
        signature = signature.replace('_', '\\_')

        return ('**%s%s**\n%s%s' % (signature, annotation, self.docs, self.arg_desc)).replace('[', '\[').replace(']', '\]')

    @classmethod
    def parse_argument_descriptors(cls, raw):
        res = []
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
    REGEX = re.compile('class (?P<name>_?[a-zA-Z]+)\s?\((?P<parent>_?[a-zA-Z]+)\):\n'
                       '\s*"""\n(?P<docs>(.*\n)+?)\s*"""\n*(?P<body>(.*\n)+?(?=(\n\n)|$))')

    def __init__(self, matcher):
        self._fields = {}
        self._functions = {}
        self.name = matcher.group('name')
        self.parent = None if matcher.group('parent') == 'object' else Module.classes[matcher.group('parent')]
        self._docs = '\n'.join(map(lambda x: x.strip(), matcher.group('docs').split('\n')))

        for field_matcher in FieldDef.STATIC_REGEX.finditer(matcher.group('body')):
            name = field_matcher.group('name')
            if not name.startswith('_'):
                self._fields[name] = FieldDef(field_matcher, self.parent, static=True)

        for function_matcher in FunctionDef.REGEX.finditer(matcher.group('body')):
            name = function_matcher.group('name')
            if name == '__init__':
                self.parse_fields(function_matcher.group('body'))
            if not name.startswith('_') or (name.startswith('__') and not name == '__init__'):
                if function_matcher.group('annotation') == 'property':
                    self._fields[name] = FieldDef(function_matcher, self.parent, static=False)
                else:
                    self._functions[name] = FunctionDef(function_matcher, self.parent)

    @property
    def docs(self):
        if False and self.parent:
            return self._docs + '\n' + self.parent.docs
        else:
            return self._docs

    @property
    def functions(self):
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
        result = {}
        for field in self._fields:
            result[field] = self._fields[field]
        if self.parent:
            for field in self.parent.fields:
                if field not in self._fields:
                    result[field] = self.parent.fields[field]
        return result

    def __str__(self):
        header = '### %s' % self.name
        docs = self.docs

        field_str = '\n\n'.join(map(lambda x: str(x[1]), sorted(self.fields.items()))) + '\n' if self.fields else ''
        function_str = '\n\n'.join(map(lambda x: str(x[1]), sorted(self.functions.items()))) + '\n' if self.functions else ''
        res =  '%s\n\n%s\n\n' % (header, docs)
        if field_str:
            res += '#### Fields\n%s\n\n' % field_str
        if function_str:
            res += '#### Functions\n%s' % function_str
        return res

    def parse_fields(self, init_body):
        for field_matcher in FieldDef.REGEX_INIT.finditer(init_body):
            name = field_matcher.group('name')
            if not name.startswith('_'):
                self._fields[name] = FieldDef(field_matcher, self.parent, static=False)


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
        reference_file.write(Module.description())
        reference_file.write('## Class overview\n\n')

        for class_name in sorted(Module.classes.keys()):
            if class_name.startswith('_'):
                continue
            reference_file.write(str(Module.classes[class_name]))
            reference_file.write('\n')
