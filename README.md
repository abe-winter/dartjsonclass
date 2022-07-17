# dartjsonclass

This is a python project that takes a simple input format and outputs dart classes that can parse + generate json.

## roadmap

- [x] generate dart class
- [x] json ser/des
- [ ] generate dio interfaces

## design questions

### Why not use dart codegen to do this?

The dart codegen tools I've used aren't as seamless as I would like and require me to write a bunch of verbose stuff.

### Why target dio?

all the other have problems supporting cookies / form encoding. built in http only works when you're targeting the web I think? idk, this might be a me issue.

### Why not grpc?

I'm targeting a non-grpc backend
