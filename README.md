# dartjsonclass

This is a python project that generates dart classes from pydantic classes.

The dart classes which we output:
- convert to and from json or `Map`
- have `operator ==` and `copy`
- have basic metaprogramming features (getAttr / setAttr / fields list)
- mostly-working nesting

Play with it by running `make e2e` in the repo. This runs the tool on `example.py` and runs a (very simple) suite of dart tests to exercise capabilities.

## installation

(pip with git+)

## status

Don't use this in a prod codebase unless:
- you have simple serialization classes (not much nesting, straightforward nulls)
- you have fairly comprehensive testing around serialization in your dart codebase

Even then, you should post a github issue with your use case so we can talk about risks.

## roadmap

- [x] generic codegen / expression renderer
- [x] dart specific codegen
- [x] pydantic-to-dart
- [x] some collection support
- [x] fromMap / toMap, fromJson / toJson
- [x] basic metaprogramming: fieldNames / getAttr / setAttr
- [x] operator ==, copy, hash
  - [ ] operator == for collections (mostly working, needs comprehensive tests)
- nullable fields
  - [x] literals
  - [ ] non-literals (mostly working, needs comprehensive tests)
- [ ] nested collections like `Map<String, List<Item>>` (may be working, needs tests)
- [ ] tests passing, coverage, CI

### nice-to-haves

- [ ] plugin system for types and error-handling
- [ ] ISO datetimes plugin
- [ ] fromDioRequest factory
- [ ] generate inheritance that matches pydantic (probably only base class testing, though composition with spread ops is possible)
