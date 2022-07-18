import contextlib
from dataclasses import dataclass
from typing import List, Literal
from .parser import DartClass

class CodegenError(Exception): pass

@dataclass
class Expr:
    "AST lite"
    type: str
    kwargs: dict

    TEMPLATES = None

    @staticmethod
    def maybe_render(item):
        # note: intentional isinstance Expr, not classmethod, so different expr subclasses are compatible
        return item.render() if isinstance(item, Expr) else str(item)

    @classmethod
    def fac(cls, type_, **kwargs):
        "convenience factory"
        return cls(type=type_, kwargs=kwargs)

    def render(self) -> list:
        "returns list of tokens"
        if self.TEMPLATES is None:
            raise NotImplementedError('must define TEMPLATES in subclass')
        if self.type not in self.TEMPLATES:
            raise CodegenError(f"template not defined for type {self.type} in {type(self).__name__}")
        template = self.TEMPLATES[self.type]
        return flatten(template(**self.kwargs))

class Token: pass
class Nosp(Token): pass
class Endl(Token): pass
class Indent(Endl): pass
class Dedent(Endl): pass

def flatten(seq):
    ret = []
    for x in seq:
        if isinstance(x, (list, tuple)):
            ret.extend(flatten(x))
        else:
            ret.append(x)
    return ret

def ajoin(seq, delim=','):
    "like string.join, but for an array"
    ret = []
    if not seq:
        return ret
    for i, x in enumerate(seq):
        ret.append(x)
        if i < len(seq) - 1:
            if isinstance(delim, (list, tuple)):
                ret.extend(delim)
            else:
                ret.append(delim)
    return ret

def flag(name, active):
    return name if active else None

class DartExpr(Expr):
    # todo: indentation awareness for lines; some kind of 'line preference' wrapper response
    # todo: make these decorated methods as well so they can be more complicated
    TEMPLATES = {
        'call': lambda name, args=(): [name, Nosp, '(', Nosp, args and Expr.maybe_render(args), Nosp, ')'],
        'opt': lambda child: [Expr.maybe_render(child), Nosp, '?'],
        'sig': lambda name, ret=None, args=None, factory=False: [ret, flag('factory', factory), name, Nosp, '(', Nosp, args and Expr.maybe_render(args), Nosp, ')'],
        'list': lambda children, delim=(Nosp, ','): ajoin(children, delim),
        'block': lambda sig, body=None: [Expr.maybe_render(sig), '{}' if body is None else ['{', Indent, Expr.maybe_render(body), Dedent, '}']],
        'arg': lambda type, name: [type, name],
        'member': lambda type, name: [type, name, Nosp, ';', Endl],
        'classdec': lambda name, imp=None: ['class', name, ['implements', Expr.maybe_render(imp)] if imp else None],
    }

    def opt(self):
        "wrap self in optional. you can use this as a static method too to wrap a string"
        return DartExpr.fac('opt', child=self)

class Indenter(list):
    "list of strings that also manages indentation"
    def __init__(self, indent='  '):
        super().__init__()
        self.indent = indent
        self.indents = 0

    def tab(self, n):
        "change the nubmer of indents stuck onto append() calls"
        self.indents += n

    @contextlib.contextmanager
    def withtab(self, n):
        "context manager version of self.tab(), undoes at end"
        self.tab(n)
        yield
        self.tab(-n)

    def append(self, x):
        super().append(self.indent * self.indents + x)

def assert_known_type(name, cls, names):
    if name not in names:
        raise CodegenError(f"{name} ref'd by {cls.name} is not in types list {names}")

def genclass(cls: DartClass, all_type_names = ()):
    "generate dart code for DartClass"
    lines = Indenter()
    lines.append(f'class {cls.name} ' + '{') # yes {{ but my syntax highlighter doesn't support it
    lines.tab(1)
    for field in cls.fields:
        lines.append(f'{field.dart_type} {field.name};');

    # constructor
    lines.append(f'{cls.name}(' + ', '.join(f'this.{field.name}' for field in cls.fields) + ');')

    # todo: toggle '!' everywhere depending on nullability
    # todo: think about nesting, i.e. Map<String, List<X>> support, List<Map<String, X>>. fancier AST -> expression builder would make this easier

    # fromMap factory
    lines.append(f'factory {cls.name}.fromMap(Map<String, dynamic> raw) => {cls.name}(')
    with lines.withtab(1):
        for field in cls.fields:
            if field.dart_type.uses_extension_types():
                if field.dart_type.template_class is None:
                    base_type = field.dart_type.full_type.removesuffix("?")
                    assert_known_type(base_type, cls, all_type_names)
                    lines.append(f'{base_type}.fromMap(raw["{field.name}"]!),')
                elif field.dart_type.template_class == 'List':
                    base_type = field.dart_type.children[0].full_type.removesuffix("?")
                    assert_known_type(base_type, cls, all_type_names)
                    lines.append(f'raw["{field.name}"]!.map((e) => {base_type}.fromMap(e)).toList(),')
                elif field.dart_type.template_class == 'Map':
                    if field.dart_type.children[0].full_type != 'String':
                        raise CodegenError(f"we support String keys, not {field.dart_type.children[0]}, at {cls.name}.{field.name}")
                    base_type = field.dart_type.children[1].full_type.removesuffix("?")
                    assert_known_type(base_type, cls, all_type_names)
                    lines.append(f'raw["{field.name}"]!.map((key, val) => MapEntry(key, {base_type}.fromMap(val))),')
                else:
                    raise NotImplementedError(f'unk collection class {field.dart_type.template_class}')
            else:
                lines.append(f'raw["{field.name}"]!,')
    lines.append(');')

    # toMap
    lines.append('Map<String, dynamic> toMap() => Map.fromEntries([')
    with lines.withtab(1):
        for field in cls.fields:
            if field.dart_type.uses_extension_types():
                if field.dart_type.template_class is None:
                    lines.append(f'MapEntry("{field.name}", {field.name}.toMap()),')
                elif field.dart_type.template_class == 'List':
                    lines.append(f'MapEntry("{field.name}", {field.name}.map((e) => e.toMap()).toList()),')
                elif field.dart_type.template_class == 'Map':
                    lines.append(f'MapEntry("{field.name}", {field.name}.map((key, val) => MapEntry(key, val.toMap())),')
                else:
                    raise NotImplementedError(f'unk collection class {field.dart_type.template_class}')
            else:
                lines.append(f'MapEntry("{field.name}", {field.name}),')
    lines.append(']);')

    lines.tab(-1)
    lines.append('}\n')
    return '\n'.join(lines)
