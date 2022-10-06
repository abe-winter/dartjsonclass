"misc reusable codegen stuff"
import contextlib, itertools, functools
from dataclasses import dataclass
from typing import List, Literal
from .parser import DartClass, DartType

class CodegenError(Exception): pass

def expr_fac(cls, name, fn):
    "function factory for expr"
    fn.__name__ = f'x_{name}'
    @functools.wraps(fn)
    def expr_fn(*args, **kwargs):
        full_kwargs = {**dict(zip(fn.__code__.co_varnames, args)), **kwargs}
        return cls(type=name, kwargs=full_kwargs)
    return expr_fn

@dataclass
class Expr:
    "AST lite"
    type: str
    kwargs: dict

    TEMPLATES = {}

    def __init_subclass__(cls, **kwargs):
        "creates classmethods from TEMPLATES for shortcuts, and in the hope that some code inference tools will find them"
        super.__init_subclass__(**kwargs)
        # todo: it seems like jedi is trying to get runtime type mutations? debug this
        # https://github.com/davidhalter/jedi/issues/1347 dynamic class methods
        # https://github.com/davidhalter/jedi/issues/1458 use annotations
        # https://github.com/davidhalter/jedi/pull/1461 PR to use annotations
        # todo: clear error here for all expr names which are not valid identifiers
        for name, fn in cls.TEMPLATES.items():
            setattr(cls, f'x_{name}', staticmethod(expr_fac(cls, name, fn)))

    @staticmethod
    def maybe_render(item):
        # note: intentional isinstance Expr, not classmethod, so different expr subclasses are compatible
        # todo: I think this needs to walk sublists / exprs in list case
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
class Nosemi(Token): pass
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

def extapend(arr: list, delim) -> list:
    "extend or append arr with delim. if delim is list or tuple, arr gets extended. helper for ajoin."
    if isinstance(delim, (list, tuple)):
        arr.extend(delim)
    else:
        arr.append(delim)
    return arr

def ajoin(seq, delim=',', final=None) -> list:
    """
    Like string.join, but returns a list with tokens stuck in.
    Some flattening happening?
    Final is the delim for after last elt (like ';'? why?).
    """
    ret = []
    if not seq:
        return ret
    next_delim = None
    for x in seq:
        if next_delim is not None:
            extapend(ret, delim)
        ret.append(x)
        next_delim = delim
    if final is not None:
        extapend(ret, final)
    return ret

def flag(name, active, default=None):
    # wtf is this for, past me
    return name if active else default

def format_exprs(tokens: list, indent='  ') -> List[str]:
    "format list of tokens to a list of lines"
    endl_dedents = [i for i, pair in enumerate(itertools.pairwise(tokens)) if pair == (Endl, Dedent)]
    if endl_dedents:
        # coalesce dedents
        for i, index in enumerate(endl_dedents):
            index -= i # because we are removing things
            tokens[index:index + 2] = (Dedent,)
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
        # filter None here bc (tok, None, Nosp) breaks Nosp detection
        linetok = list(filter(lambda x: x is not None, linetok))
        for i, tok in enumerate(linetok):
            # todo: get rid of '', but set up tests first
            if tok in (Nosp, ''):
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
        # todo: make these 'adjacent pair' rules linear + faster
        while Nosemi in line:
            index = line.index(Nosemi)
            line[index:index + 2] = []
        lines.append(''.join(line))
    return lines
