"example for testing"
import uuid
from typing import List, Dict, Optional
import pydantic

class Item(pydantic.BaseModel):
    a: int
    b: str

class Msg(pydantic.BaseModel):
    id: str
    maybe: Optional[int]
    item: Item
    item_list: List[Item]
    item_dict: Dict[str, Item]
    id_dict: Dict[uuid.UUID, Item]
