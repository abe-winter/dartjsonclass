"use pydantic classes as a source"

import importlib.util, uuid
from typing import _GenericAlias
import pydantic
from .parser import DartClass, DartField
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

def dart_type(py_type: type, nullable: bool = False) -> str:
    # careful: List[int] isn't a subclass of type
    raise NotImplementedError('todo: this needs to be some kind of type object, not a str')
    if nullable:
        # warning: are there other Optional cases I'm not picking up? List[Optional[int]], for example
        return f'{dart_type(py_type)}?'
    if py_type is int:
        return 'int'
    elif py_type is float:
        raise NotImplementedError('floats?')
    elif py_type in (str, uuid.UUID):
        return 'String'
    elif isinstance(py_type, _GenericAlias):
        if py_type.__origin__ is list:
            assert len(py_type.__args__) == 1
            return f'List<{dart_type(py_type.__args__[0])}>'
        elif py_type.__origin__ is dict:
            assert len(py_type.__args__) == 2
            key, val = py_type.__args__
            return f'Map<{dart_type(key)}, {dart_type(val)}>'
        else:
            raise TypeError('unk collection type', py_type.__origin__)
    elif isinstance(py_type, type) and issubclass(py_type, pydantic.BaseModel):
        # assume this is a tracked type. todo: eventually complain if it's not a known type
        return py_type.__name__
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
