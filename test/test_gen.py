from dartjsonclass.gen import DartExpr, ajoin, flatten, Nosp, Endl, Indent, Dedent

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
        ['func', Nosp, '(', Nosp, '1', Nosp, ',', 2, Nosp, ',', '"three"', Nosp, ')']
    assert DartExpr.opt('String').render() == ['String', Nosp, '?']
    assert DartExpr.fac('block',
        sig=DartExpr.fac('sig', name='f'),
    ).render() == [None, None, 'f', Nosp, '(', Nosp, None, Nosp, ')', '{}']
