"misc reusable codegen stuff"
import contextlib
from dataclasses import dataclass
from typing import List, Literal
from .parser import DartClass, DartType

class CodegenError(Exception): pass

@dataclass
class Expr:
    "AST lite"
    type: str
    kwargs: dict

    TEMPLATES = {}

    @staticmethod
    def maybe_render(item):
        # note: intentional isinstance Expr, not classmethod, so different expr subclasses are compatible
        return item.render() if isinstance(item, Expr) else str(item)

    @classmethod
    def fac(cls, type_, **kwargs):
        "convenience factory"
        return cls(type=type_, kwargs=kwargs)

    @classmethod
    def fac2(cls, type_, *args):
        "like fac() but infers kwargs from TEMPLATES"
        template = cls.TEMPLATES[type_]
        kwargs = dict(zip(template.__code__.co_varnames, args))
        return cls.fac(type_, **kwargs)

    def render(self) -> list:
        "returns list of tokens"
        if self.type not in self.TEMPLATES:
            raise CodegenError(f"template not defined for type {self.type} in {type(self).__name__}")
        template = self.TEMPLATES[self.type]
        return flatten(template(**self.kwargs))

class Token: pass
class Nosp(Token): pass
class Endl(Token): pass
class Indent(Endl): pass
class Dedent(Endl): pass

def flatten(seq):
    ret = []
    for x in seq:
        if isinstance(x, (list, tuple)):
            ret.extend(flatten(x))
        else:
            ret.append(x)
    return ret

def ajoin(seq, delim=',', final=None) -> list:
    """
    Like string.join, but returns a list with tokens stuck in.
    Some flattening happening?
    Final is the delim for after last elt (like ';'? why?).
    """
    ret = []
    if not seq:
        return ret
    for i, x in enumerate(seq):
        ret.append(x)
        if i == len(seq) - 1:
            idelim = final
        else:
            idelim = delim
        if idelim is None:
            continue
        if isinstance(idelim, (list, tuple)):
            ret.extend(idelim)
        else:
            ret.append(idelim)
    return ret

def flag(name, active, default=None):
    # wtf is this for, past me
    return name if active else default

def format_exprs(tokens: list, indent='  ') -> List[str]:
    "format list of tokens to a list of lines"
    byline = [[]]
    for tok in tokens:
        if tok in (Indent, Dedent, Endl):
            byline.append([tok])
        else:
            byline[-1].append(tok)
    lines = []
    nindent = 0
    for linetok in byline:
        line = []
        for i, tok in enumerate(linetok):
            if tok in (Nosp, None, ''):
                continue
            elif tok in (Endl, Indent, Dedent):
                if tok is Indent:
                    nindent += 1
                if tok is Dedent:
                    nindent -= 1
                line.append(nindent * indent)
            elif i == len(linetok) - 1 or linetok[i + 1] is Nosp:
                line.append(tok)
            else:
                line.extend((tok, ' '))
        lines.append(''.join(line))
    return lines
