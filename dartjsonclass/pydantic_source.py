"use pydantic classes as a source"

import importlib.util, uuid, os, enum, warnings
from typing import _GenericAlias, Literal, Union
from datetime import datetime
import pydantic
from .parser import DartClass, DartField, DartType
from .dartgen import genclass

def path_to_module(path: str) -> str:
    "convert path to dotted module; probably brittle"
    # there must be an easier way to do this
    assert not os.path.isabs(path)
    return path.removesuffix('.py').replace('/', '.')

def classes_in_module(path):
    "return list of BaseModel subclasses in module"
    mod = importlib.import_module(path_to_module(path))
    return [
        value
        for _key, value in mod.__dict__.items()
        if isinstance(value, type) and issubclass(value, pydantic.BaseModel)
    ]

def safe_subclass(cls, parent):
    "safe issubclass wrapper"
    return isinstance(cls, type) and issubclass(cls, parent)

def dart_type(py_type: type, nullable: bool = False) -> DartType:
    # warning: are there other Optional cases I'm not picking up? List[Optional[int]], for example
    # careful: List[int] isn't a subclass of type
    # todo: (t: Literal['u'] = 'u') thinks it's optional but isn't. is the default confusing it?
    null_tail = '?' if nullable else ''
    if py_type is int or safe_subclass(py_type, pydantic.types.ConstrainedInt):
        return DartType('int' + null_tail, nullable)
    elif py_type is float:
        return DartType('double' + null_tail, nullable)
    elif py_type in (str, uuid.UUID) or safe_subclass(py_type, pydantic.types.ConstrainedStr):
        return DartType('String' + null_tail, nullable)
    elif py_type is bool:
        return DartType('bool' + null_tail, nullable)
    elif py_type is datetime:
        return DartType('DateTime' + null_tail, nullable)
    elif isinstance(py_type, _GenericAlias):
        if py_type.__origin__ is list:
            assert len(py_type.__args__) == 1
            inner = dart_type(py_type.__args__[0])
            return DartType(
                f'List<{inner.full_type}>{null_tail}',
                nullable,
                'List',
                [inner],
                is_ext=inner.is_ext,
            )
        elif py_type.__origin__ is dict:
            assert len(py_type.__args__) == 2
            key, val = map(dart_type, py_type.__args__)
            assert key.full_type == 'String'
            return DartType(
                f'Map<{key.full_type}, {val.full_type}>{null_tail}',
                nullable,
                'Map',
                [key, val], # is this right? or should it be val
                is_ext=val.is_ext,
            )
        elif py_type.__origin__ is Literal:
            # todo: maybe enum here
            return DartType('String' + null_tail, nullable)
        elif py_type.__origin__ is Union:
            # todo: provide a way to parse the union
            # todo: does dynamic ever need to be nullable?
            return DartType('dynamic' + null_tail, nullable)
        else:
            raise TypeError('unk collection type', py_type, type(py_type), py_type.__origin__)
    elif isinstance(py_type, type) and issubclass(py_type, pydantic.BaseModel):
        # assume this is a tracked type. todo: eventually complain if it's not a known type
        return DartType(py_type.__name__ + null_tail, nullable, is_ext=True)
    elif isinstance(py_type, type) and issubclass(py_type, enum.Enum):
        # todo: register this globally so we know to generate an enum for it, then ref the type
        return DartType('String' + null_tail, nullable)
    elif py_type is list:
        # todo: include source class in warning
        warnings.warn('bare list, using List but this is probably bad')
        return DartType('List' + null_tail, nullable)
    elif py_type is dict:
        # todo: include source class in warning
        warnings.warn('bare dict, ideally type this')
        return DartType('Map<String, dynamic>' + null_tail, nullable)
    else:
        raise NotImplementedError('unk whatever', py_type)

def pydantic_to_dart(cls: pydantic.BaseModel):
    "wrapper for dart genclass"
    assert issubclass(cls, pydantic.BaseModel)
    return DartClass(name=cls.__name__, fields=[
        # outer_type_ is List[int], type_ will be int. ugh this cost me 30 minutes.
        # note: use .allow_none, *not* .required. required will be false for non-nullable fields with a default or defalut_factory set.
        DartField(dart_type(field.outer_type_, field.allow_none), field.name)
        for field in cls.__fields__.values()
    ])

def dep_classes(cls: pydantic.BaseModel, seen: set = None):
    "list of classes that are dependencies of this one"
    # todo: high pri for test coverage
    seen = seen if seen is not None else set()
    ret = []
    for field in cls.__fields__.values():
        if safe_subclass(field.type_, pydantic.BaseModel):
            if field.type_ in seen:
                continue
            ret.append(field.type_)
            seen.add(field.type_)
            ret.extend(dep_classes(field.type_, seen))
    return ret
