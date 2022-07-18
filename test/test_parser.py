import pytest
from dartjsonclass.parser import DartType, scoped_split

def test_scoped_split():
    assert ['a', 'b'] == scoped_split('a, b')
    assert ['a', 'b<c, d>', 'e'] == scoped_split('a, b<c, d>, e')
    with pytest.raises(AssertionError):
        scoped_split('a, b<c, <d>, e')
    with pytest.raises(AssertionError):
        scoped_split('<>>')

def test_type_parser():
    dt = DartType.parse('String')
    assert not dt.nullable

    dt = DartType.parse('String?')
    assert dt.nullable
    assert not dt.uses_extension_types()

    dt = DartType.parse('Other')
    assert dt.uses_extension_types()

    dt = DartType.parse('List<String>')
    assert dt.template_class == 'List'
    assert not dt.uses_extension_types()

    dt = DartType.parse('Map<String, dynamic>')
    assert not dt.uses_extension_types()
    assert dt.template_class == 'Map'

    dt = DartType.parse('Map<String, OtherType>')
    assert dt.template_class == 'Map'
    assert dt.uses_extension_types()
