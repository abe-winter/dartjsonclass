"dart-specific codegen"
import contextlib
from .parser import DartClass
from .codegen import Expr, Nosp, flag, ajoin, Indent, Dedent, CodegenError, Endl

class DartExpr(Expr):
    # todo: indentation awareness for lines; some kind of 'line preference' wrapper response
    # todo: make these decorated methods as well so they can be more complicated
    TEMPLATES = {
        'call': lambda name, args=(), scope='()': [Expr.maybe_render(name), Nosp, scope[0], Nosp, args and Expr.maybe_render(args), Nosp, scope[1]],
        # opt is actually any unary suffix
        'opt': lambda child, op='?': [Expr.maybe_render(child), Nosp, op],
        # note: name is optional for arrow functions
        'sig': lambda name=None, ret=None, args=None, factory=False: [ret, flag('factory', factory), name, Nosp, '(', Nosp, args and Expr.maybe_render(args), Nosp, ')'],
        # comma list
        'list': lambda children, delim=(Nosp, ','): ajoin(list(map(Expr.maybe_render, children)), delim),
        # list literal
        'listl': lambda children: ['[', Nosp, ajoin(list(map(Expr.maybe_render, children)), (Nosp, ',')), Nosp, ']'],
        'block': lambda sig, children: [Expr.maybe_render(sig), '{}' if not children else ['{', Indent, ajoin(list(map(Expr.maybe_render, children)), (Nosp, ';', Endl), final=(Nosp, ';')), Dedent, '}']],
        'arrow': lambda sig, body: [Expr.maybe_render(sig), '=>', Expr.maybe_render(body)],
        'arg': lambda type, name: [type, name],
        'member': lambda type, name: [type, name],
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

    @classmethod
    def list(cls, children):
        "compact helper for constructing lists"
        return cls.fac('list', children=children)

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

def genclass(cls: DartClass, all_type_names = ()) -> DartExpr:
    "generate dart code for DartClass"
    # lines.append(f'class {cls.name} ' + '{') # yes '{{', but my syntax highlighter doesn't support it
    members = []
    for field in cls.fields:
        members.append(DartExpr.fac('member', type=field.dart_type.full_type, name=field.name))

    # constructor
    members.append(DartExpr.fac('sig', name=cls.name, args=DartExpr.fac('list', children=[f'this.{field.name}' for field in cls.fields])))

    # fromMap factory
    members.append(DartExpr.fac('arrow',
        sig=DartExpr.fac('sig', name=f"{cls.name}.fromMap", args=DartExpr.list(['Map<String, dynamic> raw']), factory=True),
        body=DartExpr.fac2('call', cls.name, DartExpr.list([
            field_from_map(field, cls)
            for field in cls.fields
        ])),
    ))

    members.append(DartExpr.fac('arrow',
        sig=DartExpr.fac('sig', name=f"{cls.name}.toMap", ret='Map<String, dynamic> toMap'),
        body=DartExpr.fac2('call', 'Map.fromEntries', DartExpr.fac2('listl', [
            DartExpr.fac2('call', 'MapEntry', DartExpr.list([
                f'"{field.name}"',
                field.name,
            ]))
            for field in cls.fields
        ])),
    ))

    return DartExpr.fac('block',
        sig=DartExpr.fac2('classdec', cls.name),
        children=members,
    )

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
