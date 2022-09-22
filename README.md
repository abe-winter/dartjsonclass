# dartjsonclass

This is a python project that takes a simple input format and outputs dart classes that can parse + generate json.

## roadmap

- [x] generate dart class
- [x] some collection support
- [ ] dart base class with toJsonable
- [ ] attrs / get / set
- [ ] nullable fields
- [ ] parse datetimes
- [ ] bonus: read classes from pydantic
- [ ] bonus: generate dio interfaces

Internals:

- [ ] better expression builder for easier support of nested types (`Map<String, List<CustomType>>`, for example)

## design questions

### Why not use dart codegen to do this?

The dart codegen tools I've used have not been a good fit for my working style.
