import json, re
from typing import List
from dataclasses import dataclass

class ParseError(Exception): pass

@dataclass
class DartField:
    "parser / model for fields"
    dart_type: str
    name: str

# test: Map<String, List<OtherClass>>
RE_FIELD = re.compile(r'((\w+)(<.+>)?\??)\s+([\w_]+)$')

@dataclass
class DartClass:
    "parser / model for classes"
    name: str
    fields: List[DartField]

    @classmethod
    def parse(cls, name: str, raw: dict):
        fields = []
        for i, field in enumerate(raw['fields']):
            if isinstance(field, str):
                try:
                    dtype, _root_type, _template, fname = RE_FIELD.match(field).groups()
                except Exception as err:
                    raise ParseError(f'problem splitting field {i} of {name}: {field}')
                fields.append(DartField(dart_type=dtype, name=fname))
            elif isinstance(field, dict):
                fields.append(DartField(**field))
            else:
                raise TypeError(f'unk type {type(field)} for field of {name}')
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
