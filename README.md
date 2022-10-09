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
  - [ ] operator == for collections (mostly working, needs comprehensive tests)
- nullable fields
  - [x] literals
  - [ ] non-literals (mostly working, needs comprehensive tests)
- [ ] nested collections like `Map<String, List<Item>>` (may be working, needs tests)
- [ ] tests passing, coverage, CI
- [ ] format version strings into the generated .dart (including jsonbase) (version of this tool and the source codebase)
- [ ] support no-json, no-meta, no-dataclass flags (half working but JsonBase needs to be factored to 3 interfaces)
- [ ] make get/set opt-in per class (it's the largest feature by line count, also probably the least-used)
- [ ] rehydrate union types (instead of making them dynamic)

### nice-to-haves

- [ ] global and per-class immutable
- [ ] factory with named arguments, copyWith
- [ ] walk tree to render DartExprs from root render, don't require pre-rendering them in codegen
- [ ] register global error handler
- [ ] ISO datetimes plugin
- [ ] fromDioResponse factory
- [ ] generate inheritance that matches pydantic (probably only for base class testing. composition with spread ops is possible but complicated)

## other useful features

- [`codegen.py`](dartjsonclass/codegen.py) provides a generic tool for generating formatted source in any language from python. [`dartgen.py`](dartjsonclass/dartgen.py) has an example of how to use it
