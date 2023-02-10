import pytest
from dartjsonclass.codegen import ajoin, flatten, Nosp, Endl, Indent, Dedent, format_exprs
from dartjsonclass.dartgen import DartExpr, field_from_map, genclass, maybe_mask
from .test_parser import TEST_CLASS

def test_flatten():
    assert flatten([1]) == [1]
    assert flatten([1, [2, 3]]) == [1, 2, 3]
    assert flatten([1, [2, [3, 4]]]) == [1, 2, 3, 4]

def test_ajoin():
    assert ajoin(()) == []
    assert ajoin(['x']) == ['x']
    assert ajoin('abc', '.') == ['a', '.', 'b', '.', 'c']

def test_dart_expr():
    assert DartExpr.fac('call', name='func', args=DartExpr.fac('list', children=['1', 2, '"three"'])).render() == \
        DartExpr.fac2('call', 'func', DartExpr.list(['1', 2, '"three"'])).render() == \
        ['func', Nosp, '(', Nosp, '1', Nosp, ',', '2', Nosp, ',', '"three"', Nosp, ')']
    assert DartExpr.opt('String').render() == ['String', Nosp, '?']
    assert DartExpr.x_block(
        sig=DartExpr.x_sig(name='f'),
        children=None,
    ).render() == [None, None, 'f', Nosp, '(', Nosp, None, Nosp, ')', '{}']

    # test opt() call as staticmethod
    assert DartExpr.opt('hello').render() == ['hello', Nosp, '?']

def ffm_helper(field: str):
    "helper"
    rendered = field_from_map(TEST_CLASS.get_field(field), TEST_CLASS).render()
    return format_exprs(rendered)

def test_field_from_map():
    # note: not sure these are all right; goal for now is to exercise a bunch of cases + make sure they don't crash.
    # the dart test suite tests logic for a bunch of these cases; need to normalize the cases between the two of them
    assert ffm_helper('str') == ['raw["str"]!']
    assert ffm_helper('optstr') == ['raw["optstr"]']
    assert ffm_helper('lstr') == ['[...raw["lstr"]]']
    assert ffm_helper('optlstr') == ['(raw["optlstr"] != null) ? [...raw["optlstr"]] : null']
    assert ffm_helper('listo') == ['raw["listo"].map<Other>((elt) => Other.fromMap(elt)).toList()']
    # todo: don't think I need a null check and elvis here
    assert ffm_helper('optlisto') == ['(raw["optlisto"] != null) ? raw["optlisto"]?.map<Other>((elt) => Other.fromMap(elt)).toList() : null']

    assert ffm_helper('mstr') == ['{...raw["mstr"]}']
    assert ffm_helper('mapo') == ['raw["mapo"].map<String, Other>((key, val) => MapEntry(key as String, Other.fromMap(val)))']
    assert ffm_helper('lli') == ['raw["lli"].map<List<Int>>((elt) => elt.map<Int>((elt) => Int.fromMap(elt)).toList()).toList()']
    assert ffm_helper('llo') == ['raw["llo"].map<List<Other>>((elt) => elt.map<Other>((elt) => Other.fromMap(elt)).toList()).toList()']
    # todo: 'builtins all the way down' should skip map()
    assert ffm_helper('lms') == ['raw["lms"].map<Map<String, String>>((elt) => {...elt}).toList()']
    assert ffm_helper('lmo') == ['raw["lmo"].map<Map<String, Other>>((elt) => elt.map<String, Other>((key, val) => MapEntry(key as String, Other.fromMap(val)))).toList()']
    # todo: 'builtins all the way down' should skip map()
    assert ffm_helper('maplstr') == ['raw["maplstr"].map<String, List<String>>((key, val) => MapEntry(key as String, [...val]))']

    assert ffm_helper('maplisto') == ['raw["maplisto"].map<String, List<Other>>((key, val) => MapEntry(key as String, val.map<Other>((elt) => Other.fromMap(elt)).toList()))']

def test_format():
    assert format_exprs(['x', Nosp, '(', Nosp, 'y', Nosp, ',', 'z', Nosp, ')']) == ['x(y, z)']
    assert format_exprs(['class X {', Indent, 'x = 10;', Endl, 'return x;', Dedent, '}']) == \
        ['class X {', '  x = 10;', '  return x;', '}']

def test_genclass():
    # exercise-only
    expr = genclass(TEST_CLASS)
    '\n'.join(format_exprs(expr.render()))

def test_gen_case():
    assert format_exprs(DartExpr.fac2('case', 'true', ['x += 1', 'x *= 3']).render()) \
        == ['case true:', '  x += 1;', '  x *= 3;', '  break;', '']

@pytest.mark.skip
def test_nosemi():
    raise NotImplementedError

def test_maybe_mask():
    assert maybe_mask([], 'name') == 'name'
    assert maybe_mask(['name'], 'name') == 'this.name'
    assert maybe_mask(['name'], 'other') == 'other'
