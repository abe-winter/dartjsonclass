"example for testing"
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Union
import pydantic

class Item(pydantic.BaseModel):
    a: int
    b: str

class Msg(pydantic.BaseModel):
    id: str
    maybe: Optional[int]
    item: Item
    dt: datetime
    item_list: List[Item]
    item_dict: Dict[str, Item]
    id_dict: Dict[uuid.UUID, Item]

class StrList(pydantic.BaseModel):
    strlist: List[str]
    strmap: Dict[str, str]

class NullItem(pydantic.BaseModel):
    item: Optional[Item]

class UnionTester(pydantic.BaseModel):
    union: Union[Item, str]
    list_union: List[Union[Item, str]]
    map_union: Dict[str, Union[Item, str]]
