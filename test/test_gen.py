from dartjsonclass.parser import DartClass
from dartjsonclass.codegen import ajoin, flatten, Nosp, Endl, Indent, Dedent, format
from dartjsonclass.dartgen import DartExpr, field_from_map
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
    assert DartExpr.fac('block',
        sig=DartExpr.fac('sig', name='f'),
    ).render() == [None, None, 'f', Nosp, '(', Nosp, None, Nosp, ')', '{}']

    # test opt() call as staticmethod
    assert DartExpr.opt('hello').render() == ['hello', Nosp, '?']

def ffm_helper(field: str):
    "helper"
    rendered = field_from_map(TEST_CLASS.get_field(field), TEST_CLASS).render()
    return format(rendered)

def test_field_from_map():
    assert ffm_helper('str') == ['raw["str"]!']
    assert ffm_helper('optstr') == ['raw["optstr"]']
    assert ffm_helper('lstr') == ['raw["lstr"]!']
    assert ffm_helper('optlstr') == ['raw["optlstr"]']
    assert ffm_helper('listo') == ['raw["listo"].map((elt) => elt.fromMap())']
    assert ffm_helper('optlisto') == ['raw["optlisto"]?.map((elt) => elt.fromMap())']
    assert ffm_helper('mstr') == ['raw["mstr"]!']
    assert ffm_helper('mapo') == ['raw["mapo"].map((key, val) => MapEntry(key, val.fromMap()))']
    # todo: 'builtins all the way down' should skip map()
    assert ffm_helper('lli') == ['raw["lli"].map((elt) => elt)']
    assert ffm_helper('llo') == ['raw["llo"].map((elt) => elt.map((elt) => elt.fromMap()))']
    # todo: 'builtins all the way down' should skip map()
    assert ffm_helper('lms') == ['raw["lms"].map((elt) => elt)']
    assert ffm_helper('lmo') == ['raw["lmo"].map((elt) => elt.map((key, val) => MapEntry(key, val.fromMap())))']
    # todo: 'builtins all the way down' should skip map()
    assert ffm_helper('maplstr') == ['raw["maplstr"].map((key, val) => MapEntry(key, val))']
    assert ffm_helper('maplisto') == ['raw["maplisto"].map((key, val) => MapEntry(key, val.map((elt) => elt.fromMap())))']

def test_format():
    assert format(['x', Nosp, '(', Nosp, 'y', Nosp, ',', 'z', Nosp, ')']) == ['x(y, z)']
    assert format(['class X {', Indent, 'x = 10;', Endl, 'return x;', Dedent, '}']) == \
        ['class X {', '  x = 10;', '  return x;', '}']
