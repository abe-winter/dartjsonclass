# dartjsonclass

This is a python project that takes a simple input format and outputs dart classes that can parse + generate json.

## roadmap

- [x] generate dart class
- [x] json ser/des
- [x] some collection support
- [ ] nullable fields
- [ ] parse datetimes
- [ ] generate dio interfaces

Internals:

- [ ] better expression builder for easier support of nested types (`Map<String, List<CustomType>>`, for example)

## design questions

### Why not use dart codegen to do this?

The dart codegen tools I've used are slow to run + require me to write fairly verbose dart.

### Why target dio?

all the other have problems supporting cookies / form encoding. built in http only works when you're targeting the web I think? idk, this might be a me issue.

### Why not grpc?

I'm targeting a non-grpc backend.
