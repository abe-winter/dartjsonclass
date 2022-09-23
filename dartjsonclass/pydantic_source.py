"use pydantic classes as a source"

import importlib.util, uuid
from typing import _GenericAlias
import pydantic
from .parser import DartClass, DartField, DartType
from .dartgen import genclass

def classes_in_module(path):
    "return list of BaseModel subclasses in module"
    spec = importlib.util.spec_from_file_location('djmodule', 'example.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [
        value
        for _key, value in mod.__dict__.items()
        if isinstance(value, type) and issubclass(value, pydantic.BaseModel)
    ]

def dart_type(py_type: type, nullable: bool = False) -> DartType:
    # warning: are there other Optional cases I'm not picking up? List[Optional[int]], for example
    # careful: List[int] isn't a subclass of type
    if py_type is int:
        return DartType('int', nullable)
    elif py_type is float:
        raise NotImplementedError('floats?')
    elif py_type in (str, uuid.UUID):
        return DartType('String', nullable)
    elif isinstance(py_type, _GenericAlias):
        if py_type.__origin__ is list:
            assert len(py_type.__args__) == 1
            inner = dart_type(py_type.__args__[0])
            return DartType(
                f'List<{inner.full_type}>',
                nullable,
                'List',
                [inner],
            )
        elif py_type.__origin__ is dict:
            assert len(py_type.__args__) == 2
            key, val = map(dart_type, py_type.__args__)
            return DartType(
                f'Map<{key.full_type}, {val.full_type}>',
                nullable,
                'Map',
                [key, val], # is this right? or should it be val
            )
        else:
            raise TypeError('unk collection type', py_type.__origin__)
    elif isinstance(py_type, type) and issubclass(py_type, pydantic.BaseModel):
        # assume this is a tracked type. todo: eventually complain if it's not a known type
        return DartType(py_type.__name__, nullable)
    else:
        raise NotImplementedError('unk whatever', py_type)

def pydantic_to_dart(cls: pydantic.BaseModel):
    "wrapper for dart genclass"
    assert issubclass(cls, pydantic.BaseModel)
    return DartClass(name=cls.__name__, fields=[
        # outer_type_ is List[int], type_ will be int. ugh this cost me 30 minutes.
        DartField(dart_type(field.outer_type_, not field.required), field.name)
        for field in cls.__fields__.values()
    ])
