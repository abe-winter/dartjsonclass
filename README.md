# dartjsonclass

This is a python project that generates dart classes from pydantic classes.

The dart classes which we output:
- convert to and from json or `Map`
- have `operator ==` and `copy`
- have basic metaprogramming features (getAttr / setAttr / fields list)
- mostly-working nesting

Play with it by running `make e2e` in the repo. This runs the tool on `example.py` and runs a (very simple) suite of dart tests to exercise capabilities.

Also run `make dart-test` to run a more comprehensive suite of dart tests on the generated classes.

## installation

(pip with git+)

## example

given this input in python:

```python
class Msg(pydantic.BaseModel):
    id: str
    maybe: Optional[int]
    item: Item
    dt: datetime
    item_list: List[Item]
    item_dict: Dict[str, Item]
    id_dict: Dict[uuid.UUID, Item]

```

you will get this dart (and you can suppress getAttr / setAttr, which are the bulkiest methods here, if you don't need them):

```dart
class Msg extends JsonBaseMeta {
  String id;
  int? maybe;
  Item item;
  DateTime dt;
  List<Item> item_list;
  Map<String, Item> item_dict;
  Map<String, Item> id_dict;
  Msg(this.id, this.maybe, this.item, this.dt, this.item_list, this.item_dict, this.id_dict);
  factory Msg.fromMap(Map<String, dynamic> raw) => Msg(raw["id"]!, raw["maybe"], Item.fromMap(raw["item"]), DateTime.parse(raw["dt"]), raw["item_list"].map<Item>((elt) => Item.fromMap(elt)).toList(), raw["item_dict"].map<String, Item>((key, val) => MapEntry(key as String, Item.fromMap(val))), raw["id_dict"].map<String, Item>((key, val) => MapEntry(key as String, Item.fromMap(val))));
  factory Msg.fromJson(String raw) => Msg.fromMap(jsonDecode(raw));
  @override
  Map<String, dynamic> toMap() => Map.fromEntries([MapEntry("id", id), MapEntry("maybe", maybe), MapEntry("item", item.toMap()), MapEntry("dt", dt.toIso8601String()), MapEntry("item_list", item_list.map((e) => e.toMap()).toList()), MapEntry("item_dict", item_dict.map((key, value) => MapEntry(key, value.toMap()))), MapEntry("id_dict", id_dict.map((key, value) => MapEntry(key, value.toMap())))]);
  static List<String> djc__fields = ["id", "maybe", "item", "dt", "item_list", "item_dict", "id_dict"];
  @override
  getAttr(String name) {
    switch(name) {
      case "id": return id;
      case "maybe": return maybe;
      case "item": return item;
      case "dt": return dt;
      case "item_list": return item_list;
      case "item_dict": return item_dict;
      case "id_dict": return id_dict;
      default: throw ArgumentError("Unknown field ${name}");
    } 
  } 
  @override
  void setAttr(String name, dynamic val) {
    switch(name) {
      case "id":
        id = val;
        break;
      case "maybe":
        maybe = val;
        break;
      case "item":
        item = val;
        break;
      case "dt":
        dt = val;
        break;
      case "item_list":
        item_list = val;
        break;
      case "item_dict":
        item_dict = val;
        break;
      case "id_dict":
        id_dict = val;
        break;
      default: throw ArgumentError("Unknown field ${name}");
    } 
  } 
  @override
  bool operator ==(Object other) {
    if (other is! Msg) return false;
    var x = other as Msg;
    return id == x.id && maybe == x.maybe && item == x.item && dt == x.dt && listEqual(item_list, x.item_list) && mapEqual(item_dict, x.item_dict) && mapEqual(id_dict, x.id_dict);
  } 
  @override
  int get hashCode => Object.hash(id, maybe, item, dt, hashcodeList(item_list), hashcodeMap(item_dict), hashcodeMap(id_dict));
  @override
  Msg copy() => Msg(id, maybe, item.copy(), dt, [...item_list], {...item_dict}, {...id_dict});
}
```

## status

Don't use this in a prod codebase unless:
- you have simple serialization classes (not much nesting, straightforward nulls)
- you have fairly comprehensive testing around serialization in your dart codebase

Even then, you should post a github issue with your use case so we can talk about risks and maybe add test coverage.

Known or likely problems:
- direct nesting of collection classes like `List<List<String>>`. `List<String>` is okay, `List<SomeDataclass>` is probably okay (even if SomeDataclass has collections in it)
- nullable field handling seems to be okay, but is not fully exercised in tests and I wouldn't be surprised if there are problems

## why

Various parts of my message class workflow were not working:
- codegen is slow (15ish seconds when I had 3 tools, of which I legit needed 2 probably)
- the source classes are hard to write (like I'm writing the name of the class 6 times, or inserting weird `_$_` prefixes, or defining part memberships which don't exist until I run a tool)
- generated classes are hard to extend
- parts of my codebase rely on and metaprogramming and reflectable was a pain to work with
- no one-stop shop for serialization + metaprogramming

Also, my message objects are strongly typed in my backend codebase. Maintaining them in the frontend codebase felt like duplicate work.

## roadmap

- [x] generic codegen / expression renderer
- [x] dart specific codegen
- [x] pydantic-to-dart
- [x] some collection support
- [x] fromMap / toMap, fromJson / toJson
- [x] basic metaprogramming: fieldNames / getAttr / setAttr
- [x] operator ==, copy, hash
  - [ ] operator == for collections (mostly working, needs comprehensive combination testing)
  - [x] literals
  - [ ] non-literals (mostly working, needs comprehensive tests)
  - [ ] factory with named arguments, copyWith
- [x] nullable fields
  - [ ] inventory all special cases + cover them in test suite
- [x] nested collections like `Map<String, List<Item>>`
  - [ ] cover third-level nesting in test suite
  - [ ] comprehensive tests for `List<Map>`, `Map<String, List>`, and both classes and literals in the inner collection
- [ ] tests
  - [x] CI + tests passing
  - [ ] coverage in py codebase
- [ ] format version strings into the generated .dart (including jsonbase) (include version of this tool and of the source codebase)
- [ ] support no-json, no-meta, no-dataclass flags (semi working, dart generics support is an obstacle here, need strategy that doesn't limit consumer code)
- [x] make get/set opt-in per class (it's the largest feature by line count, also probably the least-used)
- [ ] rehydrate union types (instead of making them dynamic)
  - [ ] based on literal flag
  - [ ] based on field or dynamic type testing where not ambiguous
- [ ] way of specifying configs on source classes which DJC can consume
- [x] datetime support

### nice-to-haves

- [ ] global and per-class immutable
- [ ] codegen: walk tree to render DartExprs from root render, don't require pre-rendering
- [ ] better intermediate representation for classes (don't convert directly from pydantic to DartClass)
- [ ] ser/des error handling
  - [ ] global and per-class hooks (e.g. to show a toast)
  - [ ] distinguish conversion errors from missing field errors
  - [ ] include context in error (pass down dotted address to nested parse)
- [ ] include API GET route in generated class, with template string
  - [ ] also specify query params
  - [ ] also specify non-GET routes
- [ ] generate inheritance that matches pydantic (for base testing. may need this for flagged union rehydration)
  - [ ] delegate some ser/des to base class using spread ops? tricky bc some fields may be overridden

## other useful features

- [`codegen.py`](dartjsonclass/codegen.py) provides a generic tool for generating formatted source in any language from python. [`dartgen.py`](dartjsonclass/dartgen.py) has an example of how to use it
