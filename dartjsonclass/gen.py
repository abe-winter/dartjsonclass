from typing import List
from .parser import DartClass

class Indenter(list):
    def __init__(self, indent='  '):
        super().__init__()
        self.indent = indent
        self.indents = 0

    def tab(self, n):
        self.indents += n

    def append(self, x):
        super().append(self.indent * self.indents + x)

def genclass(cls: DartClass):
    "generate dart code for DartClass"
    lines = Indenter()
    lines.append(f'class {cls.name} {{')
    lines.tab(1)
    for field in cls.fields:
        lines.append(f'{field.dart_type} {field.name};');
    lines.append(f'{cls.name}(' + ', '.join(f'this.{field.name}' for field in cls.fields) + ');')
    lines.append(f'factory {cls.name}.fromMap(Map<String, dynamic> raw) => {cls.name}(')
    lines.tab(1)
    for field in cls.fields:
        # todo: specialize date parser
        lines.append(f'raw["{field.name}"]!,')
    lines.tab(-1)
    lines.append(');')
    lines.append('Map<String, dynamic> toMap() => Map.fromEntries([')
    lines.tab(1)
    for field in cls.fields:
        if field.dart_type == 'DateTime':
            raise NotImplementedError('date to string serialization')
        else:
            lines.append(f'MapEntry("{field.name}", {field.name}),')
    lines.tab(-1)
    lines.append(']);')
    lines.tab(-1)
    lines.append('}\n')
    return '\n'.join(lines)
