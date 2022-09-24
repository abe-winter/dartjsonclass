# dartjsonclass

This is a python project that takes a simple input format and outputs dart classes that can parse + generate json.

## installation

(pip with git+)

## roadmap

- [x] generic codegen / expression renderer
- [x] dart specific codegen
- [x] pydantic-to-dart
- [x] some collection support
- [x] fromMap / toMap, fromJson / toJson
- [x] basic metaprogramming: fieldNames / getAttr / setAttr
- [ ] operator=, copy, copyWith, hash
- nullable fields
  - [x] literals
  - [ ] non-literals
- [ ] nested collections like `Map<String, List<Item>>` (may be working, needs tests)
- [ ] plugin system for types and error-handling
- [ ] ISO datetimes plugin
- [ ] fromDioRequest factory
