"dart-specific codegen"
import contextlib
from typing import Callable
from .parser import DartClass, DartType, DartField
from .codegen import Expr, Nosp, Nosemi, flag, ajoin, Indent, Dedent, CodegenError, Endl

class DartExpr(Expr):
    # todo: indentation awareness for lines; some kind of 'line preference' wrapper response
    # todo: make these decorated methods as well so they can be more complicated
    # todo: why are these calling maybe_render? top-level render should walk the tree
    # todo: metaclass / subclass hook to make x_{exprname} classmethods
    TEMPLATES = {
        'call': lambda name, args=(), scope='()': [
            Expr.maybe_render(name), Nosp, scope[0], Nosp, args and Expr.maybe_render(args), Nosp, scope[1]
        ],
        # opt is actually any unary suffix
        'opt': lambda child, op='?': [Expr.maybe_render(child), Nosp, op],
        # note: name is optional for arrow functions
        'sig': lambda name=None, ret=None, args=None, factory=False: [
            ret, flag('factory', factory), name, Nosp, '(', Nosp, args and Expr.maybe_render(args), Nosp, ')'
        ],
        # comma list
        'list': lambda children, delim=(Nosp, ','): ajoin(map(Expr.maybe_render, children), delim),
        # list literal
        'listl': lambda children: ['[', Nosp, ajoin(map(Expr.maybe_render, children), (Nosp, ',')), Nosp, ']'],
        # pass nosemi=Nosemi for no semi at end
        'block': lambda sig, children, delim=(Nosp, ';'), endl=(Endl,), nosemi=None: [
            Expr.maybe_render(sig), '{}' if not children else [
                '{', Indent, ajoin(map(Expr.maybe_render, children), delim + endl, final=delim), Dedent, '}', nosemi,
            ]
        ],
        'arrow': lambda sig, body: [Expr.maybe_render(sig), '=>', Expr.maybe_render(body)],
        # list argument I guess? this is a subset of member, right?
        'arg': lambda type, name: [type, name],
        'member': lambda type, name, init=None: [type, name, '=' if init else None, init and Expr.maybe_render(init)],
        'classdec': lambda name, ext=None, imp=None: [
            'class', name,
            ['implements', Expr.maybe_render(imp)] if imp else None,
            ['extends', Expr.maybe_render(ext)] if ext else None,
        ],
        'dot': lambda obj, field, elvis=False: [Expr.maybe_render(obj), Nosp, flag('?.', elvis, '.'), Nosp, field],
        'case': lambda cond, stmts, nobreak=False: [
            'case' if cond else 'default', cond and Expr.maybe_render(cond), Nosp, ':', Indent if len(stmts) + int(not nobreak) > 1 else None,
            ajoin(map(Expr.maybe_render, stmts), (Nosp, ';', Endl), final=(Nosp, ';')),
            [Endl, 'break;'] if not nobreak else None,
            Dedent if len(stmts) + int(not nobreak) > 1 else Endl,
        ],
        # for return, await
        'kw': lambda kw, val: [kw, Expr.maybe_render(val)],
        'assign': lambda left, right: [left, '=', right],
        'bin': lambda left, op, right: [left, op, right],
        'decorate': lambda decorator, expr: ['@', Nosp, Expr.maybe_render(decorator), Endl, Expr.maybe_render(expr)],
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

DART_LITERALS = ['String', 'int']

def ffm_collectionify(dart_type: DartType, value: DartExpr):
    "helper for field_from_map, handles nesting"
    if not dart_type.template_class:
        base = dart_type.full_type.removesuffix('?')
        assert base not in DART_LITERALS # shouldn't get here
        return DartExpr.fac2('call',
            f'{dart_type.full_type}.fromMap',
            DartExpr.fac2('list', [value]),
        )
    if dart_type.template_class == 'List':
        if dart_type.children[0].base() in DART_LITERALS:
            return value # i.e. json value is fine
        else:
            return DartExpr.fac2('call', DartExpr.fac2('dot',
                DartExpr.fac('call',
                    # no idea why template specialization is necessary here -- map() seems to respect return type of predicate
                    name=DartExpr.fac('dot', obj=value, field=f'map<{dart_type.children[0].full_type}>', elvis=dart_type.nullable),
                    args=DartExpr.fac('list', children=[
                        DartExpr.fac('arrow',
                            sig=DartExpr.fac('sig', args=DartExpr.fac('list', children=['elt'])),
                            body=ffm_collectionify(dart_type.children[0], 'elt'),
                        )
                    ])
                ),
                'toList',
            ))
    elif dart_type.template_class == 'Map':
        if dart_type.children[0].full_type != 'String':
            raise CodegenError(f'maps have to have string keys, got {dart_type.children[0].full_type}')
        if dart_type.children[1].base() in DART_LITERALS:
            return value # i.e. json value is fine
        else:
            return DartExpr.fac('call',
                name=DartExpr.fac('dot', obj=value, field=f'map<String, {dart_type.children[1].full_type}>', elvis=dart_type.nullable),
                args=DartExpr.fac('list', children=[
                    DartExpr.fac('arrow',
                        sig=DartExpr.fac('sig', args=DartExpr.fac('list', children=['key', 'val'])),
                        body=DartExpr.fac('call', name='MapEntry', args=DartExpr.fac('list', children=['key as String', ffm_collectionify(dart_type.children[1], 'val')])),
                    )
                ])
            )
    else:
        raise CodegenError(f'unk collection class {dart_type.template_class}')

def field_from_map(field: DartField, cls: DartClass) -> DartExpr:
    "generate fromMap expr for a field"
    dart_type = field.dart_type
    expr = DartExpr.fac('call', name='raw', args=DartExpr.fac('list', children=[f'"{field.name}"']), scope='[]')
    if dart_type.uses_extension_types():
        return ffm_collectionify(field.dart_type, expr)
    else:
        return expr if dart_type.nullable else expr.bang()

def field_tomap(field: DartField) -> DartExpr:
    "toMap expr for a field"
    # todo: test nullable cases here and in fromMap, including nested
    if (tmpclass := field.dart_type.template_class):
        if tmpclass == 'List':
            return DartExpr.fac2('call', DartExpr.fac2('dot',
                DartExpr.fac2('call',
                    DartExpr.fac2('dot', field.name, 'map'),
                    DartExpr.fac2('arrow',
                        '(e)',
                        field_tomap(DartField(name='e', dart_type=field.dart_type.children[0])),
                    )
                ),
                'toList',
            ))
        elif tmpclass == 'Map':
            return DartExpr.fac2('call',
                DartExpr.fac2('dot', field.name, 'map'),
                DartExpr.list([DartExpr.fac2('arrow',
                    '(key, value)',
                    DartExpr.fac2('call', 'MapEntry', DartExpr.list([
                        'key',
                        field_tomap(DartField(name='value', dart_type=field.dart_type.children[1]))
                    ]))
                )]),
            )
        else:
            raise NotImplementedError('unhandled template class', tmpclass)
    elif field.dart_type.is_ext:
        return DartExpr.fac2('call', DartExpr.fac2('dot', field.name, 'toMap'))
    else:
        return field.name

def genclass(cls: DartClass, all_type_names = (), jsonbase: bool = True, meta: bool = True, data: bool = True) -> DartExpr:
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
        sig=DartExpr.fac('sig', name=f"{cls.name}.fromJson", args=DartExpr.list(['String raw']), factory=True),
        body=DartExpr.fac2('call', f"{cls.name}.fromMap", DartExpr.list([
            DartExpr.fac2('call', 'jsonDecode', DartExpr.list(['raw'])),
        ])),
    ))

    # toMap function
    members.append(DartExpr.fac('arrow',
        sig=DartExpr.fac('sig', name="toMap", ret='Map<String, dynamic>'),
        body=DartExpr.fac2('call', 'Map.fromEntries', DartExpr.fac2('listl', [
            DartExpr.fac2('call', 'MapEntry', DartExpr.list([
                f'"{field.name}"',
                field_tomap(field)
            ]))
            for field in cls.fields
        ])),
    ))

    if meta:
        members.append(DartExpr.fac2('member', 'static List<String>', 'djc__fields', DartExpr.fac2('listl', [
            f'"{field.name}"' for field in cls.fields
        ])))
        members.append(getattr_setattr(
            cls,
            DartExpr.fac('sig', name='getAttr', args=DartExpr.list(['String name'])),
            lambda field: DartExpr.fac2('kw', 'return', field.name),
            True,
        ))
        members.append(getattr_setattr(
            cls,
            DartExpr.fac('sig', name='setAttr', ret='void', args=DartExpr.list(['String name', 'dynamic val'])),
            lambda field: DartExpr.fac2('assign', field.name, 'val'),
            False,
        ))

    if data:
        members.append(DartExpr.fac('block',
            # note this isn't Object by choice, dart doesn't want to give you this
            sig=DartExpr.fac2('decorate', 'override', DartExpr.fac2('sig', 'operator ==', 'bool', DartExpr.list([f'Object other']))),
            children=[
                f'if (other is! {cls.name}) return false',
                f'var x = other as {cls.name}',
                # todo: collection customizations
                DartExpr.fac2('kw', 'return', DartExpr.fac2('list', [
                    DartExpr.fac2('bin', field.name, '==', f'x.{field.name}')
                    for field in cls.fields
                ], ('&&',))),
            ],
            nosemi=Nosemi,
        ))
        assert len(cls.fields) > 0, f"empty class {cls.name}" # body below is wrong otherwise
        members.append(DartExpr.fac('arrow',
            sig=DartExpr.fac2('decorate', 'override', 'int get hashCode'),
            body=f'{cls.fields[0].name}.hashCode' if len(cls.fields) == 1 else DartExpr.fac2('call', 'Object.hash', DartExpr.list(
                field.name for field in cls.fields
            ))
        ))
        members.append(DartExpr.fac('arrow',
            sig=f'{cls.name} copy()',
            body=DartExpr.fac2('call', cls.name, DartExpr.list(
                field.name for field in cls.fields
            ))
        ))
        # todo: copyWith
        # todo: whatever makes sorting possible

    return DartExpr.fac('block',
        sig=DartExpr.fac2('classdec', cls.name, 'JsonBase' if jsonbase else None),
        children=members,
    )

def getattr_setattr(cls: DartClass, sig: DartExpr, stmt: Callable[[DartField], DartExpr], nobreak=True):
    "common wrapper for getAttr / setAttr type switch functions"
    return DartExpr.fac('block',
        # note: this intentionally doesn't return dynamic -- I want the language to infer e.g. String return if all members are Strings
        sig=sig,
        children=[
            DartExpr.fac2('block', DartExpr.fac2('call', 'switch', DartExpr.list(['name'])), [
                DartExpr.fac2('case', f'"{field.name}"', [stmt(field)], nobreak)
                for field in cls.fields
            ] + [
                # default case
                DartExpr.fac2('case', None, [
                    DartExpr.fac2('kw', 'throw', DartExpr.fac2('call', 'ArgumentError', '"Unknown field ${name}"'))
                ], True),
            ], (), (), Nosemi),
        ],
        nosemi=Nosemi,
    )
