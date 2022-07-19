import json, re
from typing import List, Optional, Literal
import dataclasses
from dataclasses import dataclass

class ParseError(Exception): pass

# test: Map<String, List<OtherClass>>
RE_FIELD = re.compile(r'((\w+)(<.+>)?\??)\s+([\w_]+)$')
RE_TEMPLATE = re.compile(r'(\w+)(<.+>)?(\?)?')
# note: List is on the literals list as a way to hack the thing to accept untyped lists, pending the nesting system working fully. for like Map<String, List>
DART_LITERALS = Literal['String', 'Int', 'dynamic', 'List']
DART_COLLECTIONS = Literal['List', 'Map']

def scoped_split(raw: str, left: str = '<', right: str = '>', delim = ',') -> List[str]:
    "split by comma with scope awareness (<>, (), [] sort of thing). see test_parser.py for examples"
    scope = 0
    sections = []
    i = 0
    while i < len(raw):
        char = raw[i]
        if char == left:
            scope += 1
        elif char == right:
            scope -= 1
            assert scope >= 0
        elif char == delim and scope == 0:
            sections.append(raw[:i])
            raw = raw[i + 1:]
            i = 0
        i += 1
    assert scope == 0
    if len(raw):
        sections.append(raw)
    return [sec.strip() for sec in sections]

@dataclass
class DartType:
    "with template tree support"
    full_type: str
    nullable: bool = False
    template_class: Optional[str] = None
    children: List['DartType'] = dataclasses.field(default_factory=list)

    def __str__(self):
        return self.full_type

    def uses_extension_types(self) -> bool:
        "if true, this requires extra processing to translate json. if false, uses builtin types"
        return (self.template_class is None and self.full_type.removesuffix('?') not in DART_LITERALS.__args__) or \
            any(str(child) not in DART_LITERALS.__args__ for child in self.children)

    @classmethod
    def parse(cls, raw: str):
        base, template, optional = RE_TEMPLATE.match(raw).groups()
        children = []
        if template:
            subtypes = scoped_split(template[1:-1])
            children = [cls.parse(st) for st in subtypes]
        return cls(full_type=raw, template_class=base if template else None, nullable=bool(optional), children=children)

    def base(self):
        "full_type ignoring nullability"
        return self.full_type.removesuffix('?')

@dataclass
class DartField:
    "parser / model for fields"
    dart_type: DartType
    name: str

    @classmethod
    def parse(cls, raw: str):
        try:
            dtype, _root_type, _template, fname = RE_FIELD.match(raw).groups()
        except Exception as err:
            raise ParseError(f'problem splitting field {raw}')
        return DartField(dart_type=DartType.parse(dtype), name=fname)

@dataclass
class DartClass:
    "parser / model for classes"
    name: str
    fields: List[DartField]

    @classmethod
    def parse(cls, name: str, raw: dict):
        fields = []
        for i, field in enumerate(raw['fields']):
            fields.append(DartField.parse(field))
        return cls(name=name, fields=fields)

    @classmethod
    def parse_file(cls, stream):
        "entrypoint for parsing. takes an open file"
        classes = []
        for key, val in json.load(stream).items():
            if key == '_djcmeta':
                raise NotImplementedError('todo: special meta field')
            classes.append(cls.parse(key, val))
        return classes

    def get_field(self, name: str):
        "get field by name"
        for field in self.fields:
            if field.name == name:
                return field
        raise KeyError(name)
