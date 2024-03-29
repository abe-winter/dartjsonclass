"dart-specific codegen"
import contextlib
from typing import Callable, List
from .parser import DartClass, DartType, DartField
from .codegen import Expr, Nosp, Nosemi, flag, ajoin, Indent, Dedent, CodegenError, Endl

class DartExpr(Expr):
    # todo: indentation awareness for lines; some kind of 'line preference' wrapper response
    # todo: make these decorated methods as well so they can be more complicated
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
        'listl': lambda children, scope='[]': [scope[0], Nosp, ajoin(map(Expr.maybe_render, children), (Nosp, ',')), Nosp, scope[1]],
        # pass nosemi=Nosemi for no semi at end
        'block': lambda sig, children, delim=(Nosp, ';'), endl=(Endl,), nosemi=None: [
            Expr.maybe_render(sig), '{}' if not children else [
                '{', Indent, ajoin(map(Expr.maybe_render, children), delim + endl, final=delim), Dedent, '}', nosemi,
            ]
        ],
        'arrow': lambda sig, body: [Expr.maybe_render(sig), '=>', Expr.maybe_render(body)],
        # arguments list argument
        'arg': lambda type, name: [type, name],
        'member': lambda type, name, init=None: [type, name, '=' if init else None, init and Expr.maybe_render(init)],
        'classdec': lambda name, imp=None, ext=None: [
            'class', name,
            ['extends', Expr.maybe_render(ext)] if ext else None,
            ['implements', Expr.maybe_render(imp)] if imp else None,
        ],
        'dot': lambda obj, field, elvis=False: [Expr.maybe_render(obj), Nosp, flag('?.', elvis, '.'), Nosp, field],
        'case': lambda cond, stmts, nobreak=False: [
            'case' if cond else 'default', cond and Expr.maybe_render(cond), Nosp, ':', Indent if len(stmts) + int(not nobreak) > 1 else None,
            ajoin(map(Expr.maybe_render, stmts), (Nosp, ';', Endl), final=(Nosp, ';')),
            [Endl, 'break;'] if not nobreak else None,
            Dedent if len(stmts) + int(not nobreak) > 1 else Endl,
        ],
        # for return, await, spread
        'kw': lambda kw, val, sep=None: [kw, sep, Expr.maybe_render(val)],
        'assign': lambda left, right: [Expr.maybe_render(left), '=', Expr.maybe_render(right)],
        'bin': lambda left, op, right: [Expr.maybe_render(left), op, Expr.maybe_render(right)],
        'decorate': lambda decorator, expr: ['@', Nosp, Expr.maybe_render(decorator), Endl, Expr.maybe_render(expr)],
        'ternary': lambda cond, ifyes, ifno='null': ['(', Nosp, Expr.maybe_render(cond), Nosp, ')', '?', Expr.maybe_render(ifyes), ':', Expr.maybe_render(ifno)],
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
    if dart_type.full_type == 'dynamic':
        # warning: I think 'dynamic?' can happen sometimes, won't be caught here
        return value
    if not dart_type.template_class:
        base = dart_type.full_type.removesuffix('?')
        assert base not in DART_LITERALS
        return DartExpr.fac2('call',
            f'{base}.fromMap',
            DartExpr.fac2('list', [value]),
        )
    if dart_type.template_class == 'List':
        if dart_type.children[0].base() in DART_LITERALS:
            return DartExpr.fac2('listl', [DartExpr.fac2('kw', '...', value, Nosp)])
        else:
            return DartExpr.fac2('call', DartExpr.fac2('dot',
                DartExpr.fac('call',
                    # no idea why template specialization is necessary here -- map() seems to respect return type of predicate
                    name=DartExpr.fac('dot', obj=value, field=f'map<{dart_type.children[0].full_type.removesuffix("?")}>', elvis=dart_type.nullable),
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
            return DartExpr.fac2('listl', [DartExpr.fac2('kw', '...', value, Nosp)], '{}')
        else:
            return DartExpr.fac('call',
                name=DartExpr.fac('dot', obj=value, field=f'map<String, {dart_type.children[1].full_type.removesuffix("?")}>', elvis=dart_type.nullable),
                args=DartExpr.fac('list', children=[
                    DartExpr.fac('arrow',
                        sig=DartExpr.fac('sig', args=DartExpr.fac('list', children=['key', 'val'])),
                        body=DartExpr.fac('call', name='MapEntry', args=DartExpr.fac('list', children=['key as String', ffm_collectionify(dart_type.children[1], 'val')])),
                    )
                ])
            )
    else:
        raise CodegenError(f'unk collection class {dart_type.template_class}')

def arg_null_wrap(dart_type: DartType, expr: DartExpr, value: DartExpr):
    "turns f(x) with nullable x into: x != null ? f(x) : null"
    if dart_type.nullable:
        return DartExpr.fac2('ternary', DartExpr.fac2('bin', value, '!=', 'null'), expr)
    else:
        return expr

def field_from_map(field: DartField, cls: DartClass) -> DartExpr:
    "generate fromMap expr for a field"
    dart_type = field.dart_type
    expr = DartExpr.fac('call', name='raw', args=DartExpr.fac('list', children=[f'"{field.name}"']), scope='[]')
    if dart_type.uses_extension_types() or dart_type.template_class in ('List', 'Map'):
        return arg_null_wrap(dart_type, ffm_collectionify(field.dart_type, expr), expr)
    elif dart_type.full_type in ('DateTime', 'DateTime?'):
        # todo: test coverage for this case pls
        return arg_null_wrap(dart_type, DartExpr.x_call('DateTime.parse', expr), expr)
    else:
        return expr if dart_type.nullable else expr.bang()

def field_tomap(field: DartField) -> DartExpr:
    "toMap expr for a field"
    null_tail = '?' if field.dart_type.nullable else ''
    if (tmpclass := field.dart_type.template_class):
        if tmpclass == 'List':
            return DartExpr.fac2('call', DartExpr.fac2('dot',
                DartExpr.fac2('call',
                    DartExpr.fac2('dot', field.name + null_tail, 'map'),
                    DartExpr.fac2('arrow',
                        '(e)',
                        field_tomap(DartField(name='e', dart_type=field.dart_type.children[0])),
                    )
                ),
                'toList',
            ))
        elif tmpclass == 'Map':
            return DartExpr.fac2('call',
                DartExpr.fac2('dot', field.name + null_tail, 'map'),
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
        return DartExpr.fac2('call', DartExpr.fac2('dot', field.name + null_tail, 'toMap'))
    elif field.dart_type.full_type in ('DateTime', 'DateTime?'):
        return DartExpr.x_call(DartExpr.x_dot(field.name, 'toIso8601String', elvis=field.dart_type.nullable))
    else:
        return field.name

def field_equal(field: DartField) -> DartExpr:
    "generate equality test for field"
    # warning: nested collections, like List<Map>, List<List>, Map<String, List>, you get it, need to pass pred and will be always false for now
    if (tmpclass := field.dart_type.template_class) in ('Map', 'List'):
        return DartExpr.fac2('call', f'{tmpclass.lower()}Equal', DartExpr.list([field.name, f'x.{field.name}']))
    else:
        return DartExpr.fac2('bin', field.name, '==', f'x.{field.name}')

def genclass(cls: DartClass, all_type_names = (), jsonbase: bool = True, meta: bool = True, data: bool = True) -> DartExpr:
    "generate dart code for DartClass"
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
        sig=DartExpr.fac2('decorate', 'override', DartExpr.fac('sig', name="toMap", ret='Map<String, dynamic>')),
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
            lambda field: DartExpr.fac2('kw', 'return', maybe_mask(['name'], field.name)),
            True,
        ))
        members.append(getattr_setattr(
            cls,
            DartExpr.fac('sig', name='setAttr', ret='void', args=DartExpr.list(['String name', 'dynamic val'])),
            lambda field: DartExpr.fac2('assign', maybe_mask(['name', 'val'], field.name), 'val'),
            False,
        ))

    if data:
        members.append(DartExpr.fac('block',
            # note this isn't Object by choice, dart doesn't want to give you this
            sig=DartExpr.fac2('decorate', 'override', DartExpr.fac2('sig', 'operator ==', 'bool', DartExpr.list([f'Object other']))),
            children=[
                f'if (other is! {cls.name}) return false',
                # todo: 'other as {cls}' is necessary in raw dart (I think), linted as superfluous in flutter. find out why and make this optional
                f'var x = other as {cls.name}',
                # todo: collection customizations
                DartExpr.fac2('kw', 'return', DartExpr.fac2('list', map(field_equal, cls.fields), ('&&',))),
            ],
            nosemi=Nosemi,
        ))
        assert len(cls.fields) > 0, f"empty class {cls.name}" # body below is wrong otherwise
        members.append(DartExpr.x_arrow(
            sig=DartExpr.fac2('decorate', 'override', 'int get hashCode'),
            body=hash_field(cls.fields[0], True) if len(cls.fields) == 1 else DartExpr.fac2('call', 'Object.hash', DartExpr.list(
                map(hash_field, cls.fields),
            ))
        ))
        members.append(DartExpr.fac('arrow',
            sig=DartExpr.fac2('decorate', 'override', f'{cls.name} copy()'),
            body=DartExpr.fac2('call', cls.name, DartExpr.list(map(copy_field, cls.fields))),
        ))
        # todo: copyWith
        # todo: whatever makes stable sorting

    return DartExpr.x_block(
        sig=DartExpr.x_classdec(cls.name, ext=None if not jsonbase else 'JsonBaseMeta' if meta else 'JsonBase'),
        children=members,
    )

def hash_field(field: DartField, solitary: bool = False) -> DartExpr:
    "solitary means this class has 1 field and .hashCode is necessary for non-collections"
    return f'hashcodeList({field.name})' if field.dart_type.template_class == 'List' else \
        f'hashcodeMap({field.name})' if field.dart_type.template_class == 'Map' else \
        f'{field.name}.hashCode' if solitary else \
        field.name

def copy_field(field: DartField) -> DartExpr:
    "field initializer for deep copy"
    # warning: more aggressive deep copy; recurse this on child type
    dart_type = field.dart_type
    if field.dart_type.template_class == 'Map':
        return arg_null_wrap(dart_type, DartExpr.fac2('listl', [DartExpr.fac2('kw', '...', f'{field.name}{dart_type.bang_tail()}', Nosp)], '{}'), field.name)
    elif dart_type.template_class == 'List':
        return arg_null_wrap(dart_type, DartExpr.fac2('listl', [DartExpr.fac2('kw', '...', f'{field.name}{dart_type.bang_tail()}', Nosp)]), field.name)
    elif dart_type.uses_extension_types():
        return f'{field.name + dart_type.null_tail()}.copy()'
    else:
        return field.name

def getattr_setattr(cls: DartClass, sig: DartExpr, stmt: Callable[[DartField], DartExpr], nobreak=True):
    "common wrapper for getAttr / setAttr type switch functions"
    return DartExpr.fac('block',
        # note: this intentionally doesn't return dynamic -- like maybe the language will infer e.g. String return if all members are Strings
        sig=DartExpr.fac2('decorate', 'override', sig),
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

def maybe_mask(args: List[str], var: str) -> str:
    "access members this this.member when member is also a function arg"
    # todo: this needs to be automatic. codegen system needs to understand what's in scope. (this also allows minimal linting)
    return f"this.{var}" if var in args else var
