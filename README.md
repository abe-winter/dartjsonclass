# dartjsonclass

This is a python project that takes a simple input format and outputs dart classes that can parse + generate json.

## roadmap

- [x] generate dart class
- [x] some collection support
- [ ] dart JsonBase with json conversion
- [ ] fieldNames / getAttr / setAttr
- [ ] operator=, copy, copyWith, hash
- nullable fields
  - [x] literals
  - [ ] non-literals
- [ ] nested collections like `Map<String, List<Item>>`
- [ ] parse datetimes
- [x] bonus: read classes from pydantic
- [ ] bonus: generate dio interfaces

Internals:

- [ ] better expression builder for easier support of nested types (`Map<String, List<CustomType>>`, for example)
