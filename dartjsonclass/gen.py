import contextlib
from dataclasses import dataclass
from typing import List, Literal
from .parser import DartClass, DartType

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

def flag(name, active, default=None):
    return name if active else default

class DartExpr(Expr):
    # todo: indentation awareness for lines; some kind of 'line preference' wrapper response
    # todo: make these decorated methods as well so they can be more complicated
    TEMPLATES = {
        'call': lambda name, args=(), scope='()': [Expr.maybe_render(name), Nosp, scope[0], Nosp, args and Expr.maybe_render(args), Nosp, scope[1]],
        # opt is actually any unary suffix
        'opt': lambda child, op='?': [Expr.maybe_render(child), Nosp, op],
        # note: name is optional for arrow functions
        'sig': lambda name=None, ret=None, args=None, factory=False: [ret, flag('factory', factory), name, Nosp, '(', Nosp, args and Expr.maybe_render(args), Nosp, ')'],
        'list': lambda children, delim=(Nosp, ','): ajoin(list(map(Expr.maybe_render, children)), delim),
        'block': lambda sig, body=None: [Expr.maybe_render(sig), '{}' if body is None else ['{', Indent, Expr.maybe_render(body), Dedent, '}']],
        'arrow': lambda sig, body: [Expr.maybe_render(sig), '=>', Expr.maybe_render(body)],
        'arg': lambda type, name: [type, name],
        'member': lambda type, name: [type, name, Nosp, ';', Endl],
        'classdec': lambda name, imp=None: ['class', name, ['implements', Expr.maybe_render(imp)] if imp else None],
        'dot': lambda obj, field, elvis=False: [Expr.maybe_render(obj), Nosp, flag('?.', elvis, '.'), Nosp, field],
    }

    # todo: replace both of these with fac-like wrap() on base class? hmm, 'child' is not standard though
    def opt(self):
        "wrap self in optional. you can use this as a static method too to wrap a string"
        return DartExpr.fac('opt', child=self)

    def bang(self):
        "non-nullable access"
        return DartExpr.fac('opt', child=self, op='!')

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

def ffm_collectionify(dart_type: 'DartType', value: DartExpr):
    "helper for field_from_map, handles nesting"
    if not dart_type.template_class:
        base = dart_type.full_type.removesuffix('?')
        assert base not in ['String', 'Int'] # shouldn't get here
        return DartExpr.fac('call',
            name=DartExpr.fac('dot', obj=value, field='fromMap'),
        )
    if dart_type.template_class == 'List':
        if dart_type.children[0].base() in ['String', 'Int']:
            return value # i.e. json value is fine
        else:
            return DartExpr.fac('call',
                # todo: this should be elvis when nullable
                name=DartExpr.fac('dot', obj=value, field='map', elvis=dart_type.nullable),
                args=DartExpr.fac('list', children=[
                    DartExpr.fac('arrow',
                        sig=DartExpr.fac('sig', args=DartExpr.fac('list', children=['elt'])),
                        body=ffm_collectionify(dart_type.children[0], 'elt'),
                    )
                ])
            )
    elif dart_type.template_class == 'Map':
        if dart_type.children[0].full_type != 'String':
            raise CodegenError(f'maps have to have string keys, got {dart_type.children[0].full_type}')
        if dart_type.children[1].base() in ['String', 'Int']:
            return value # i.e. json value is fine
        else:
            return DartExpr.fac('call',
                name=DartExpr.fac('dot', obj=value, field='map', elvis=dart_type.nullable),
                args=DartExpr.fac('list', children=[
                    DartExpr.fac('arrow',
                        sig=DartExpr.fac('sig', args=DartExpr.fac('list', children=['key', 'val'])),
                        body=DartExpr.fac('call', name='MapEntry', args=DartExpr.fac('list', children=['key', ffm_collectionify(dart_type.children[1], 'val')])),
                    )
                ])
            )
    else:
        raise CodegenError(f'unk collection class {dart_type.template_class}')

def field_from_map(field: 'DartField', cls: 'DartClass') -> DartExpr:
    "generate fromMap expr for a field"
    dart_type = field.dart_type
    expr = DartExpr.fac('call', name='raw', args=DartExpr.fac('list', children=[f'"{field.name}"']), scope='[]')
    if dart_type.uses_extension_types():
        return ffm_collectionify(field.dart_type, expr)
    else:
        return expr if dart_type.nullable else expr.bang()
    # if field.dart_type.uses_extension_types():
    #     if field.dart_type.template_class is None:
    #         base_type = field.dart_type.full_type.removesuffix("?")
    #         assert_known_type(base_type, cls, all_type_names)
    #         lines.append(f'{base_type}.fromMap(raw["{field.name}"]!),')
    #     elif field.dart_type.template_class == 'List':
    #         base_type = field.dart_type.children[0].full_type.removesuffix("?")
    #         assert_known_type(base_type, cls, all_type_names)
    #         lines.append(f'raw["{field.name}"]!.map((e) => {base_type}.fromMap(e)).toList(),')
    #     elif field.dart_type.template_class == 'Map':
    #         if field.dart_type.children[0].full_type != 'String':
    #             raise CodegenError(f"we support String keys, not {field.dart_type.children[0]}, at {cls.name}.{field.name}")
    #         base_type = field.dart_type.children[1].full_type.removesuffix("?")
    #         assert_known_type(base_type, cls, all_type_names)
    #         lines.append(f'raw["{field.name}"]!.map((key, val) => MapEntry(key, {base_type}.fromMap(val))),')
    #     else:
    #         raise NotImplementedError(f'unk collection class {field.dart_type.template_class}')
    # else:
    #     lines.append(f'raw["{field.name}"]!,')

def genclass(cls: DartClass, all_type_names = ()):
    "generate dart code for DartClass"
    lines = Indenter()
    lines.append(f'class {cls.name} ' + '{') # yes {{ but my syntax highlighter doesn't support it
    lines.tab(1)
    members = []
    for field in cls.fields:
        members.extend(DartExpr.fac('member', type=field.dart_type.full_type, name=field.name).render())

    # constructor
    members.extend(DartExpr.fac('sig', name=cls.name, args=DartExpr.fac('list', children=[f'this.{field.name}' for field in cls.fields])).render())
    members.extend((Nosp, ';', Endl))

    # todo: toggle '!' everywhere depending on nullability
    # todo: think about nesting, i.e. Map<String, List<X>> support, List<Map<String, X>>. fancier AST -> expression builder would make this easier

    # fromMap factory
    args = []
    for field in cls.fields:
        ...
    # lines.append(f'factory {cls.name}.fromMap(Map<String, dynamic> raw) => {cls.name}(')
    members.extend(DartExpr.fac('arrow',
        sig=...,
        body=...,
    ))
    raise NotImplementedError

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

def format(tokens: list, indent='  ') -> List[str]:
    "format list of tokens to a list of lines"
    byline = [[]]
    for tok in tokens:
        if tok in (Indent, Dedent, Endl):
            byline.append([tok])
        else:
            byline[-1].append(tok)
    lines = []
    nindent = 0
    for linetok in byline:
        line = []
        for i, tok in enumerate(linetok):
            if tok in (Nosp, None, ''):
                continue
            elif tok in (Endl, Indent, Dedent):
                if tok is Indent:
                    nindent += 1
                if tok is Dedent:
                    nindent -= 1
                line.append(nindent * indent)
            elif i == len(linetok) - 1 or linetok[i + 1] is Nosp:
                line.append(tok)
            else:
                line.extend((tok, ' '))
        lines.append(''.join(line))
    return lines
