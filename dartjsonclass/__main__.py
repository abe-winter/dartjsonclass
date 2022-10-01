import argparse, sys, collections, os, shutil
from typing import List, Sequence
import pydantic
from .parser import DartClass
from .dartgen import genclass
from .codegen import format_exprs
from .pydantic_source import classes_in_module, pydantic_to_dart, dep_classes

def main():
    p = argparse.ArgumentParser()
    # todo: command to detect + clear generated files in a target dir
    p.add_argument('paths', help="list of .py or .dart files to process", nargs='+')
    p.add_argument('-o', '--output', default='-', help="destination file (default stdout)")
    p.add_argument('--mods', action='store_true', help="treat '-o' as directory, make submodules that match source layout")
    p.add_argument('--no-ser', action='store_true', help="omit json / map methods")
    p.add_argument('--no-meta', action='store_true', help="omit fields list + get/set methods")
    p.add_argument('--no-data', action='store_true', help="omit dataclass methods (copy, equal)")
    p.add_argument('--exclude', help="list of classes to exclude", nargs='+')
    p.add_argument('--include', help="list of classes to include (if none given, include all)", nargs='+')
    args = p.parse_args()

    if args.no_ser:
        raise NotImplementedError("we don't know how to omit json methods")

    classes = {}
    for path in args.paths:
        if path.endswith('.py'):
            classes[path] = classes_in_module(path)
        elif path.endswith('.dart'):
            # classes = DartClass.parse_file(open(args.path))
            raise NotImplementedError('todo: dart class parsing')
        else:
            raise ValueError(f'path {path} with unknown extension')
    by_name = {}
    prev = {}
    for path, path_classes in classes.items():
        for cls in path_classes:
            if isinstance(cls, type) and issubclass(cls, pydantic.BaseSettings):
                continue
            if cls.__name__ in args.exclude or (args.include and cls.__name__ not in args.include):
                continue
            if cls.__name__ in by_name and by_name[cls.__name__] is not cls:
                raise KeyError(f'duplicate {cls.__name__} in {path} (previous {prev[cls.__name__]})')
            by_name[cls.__name__] = cls
            prev[cls.__name__] = path
    del prev
    dart_classes = []
    for cls in by_name.values():
        dart_classes.append(pydantic_to_dart(cls))
    gen_cls = [
        genclass(cls, meta=not args.no_meta, data=not args.no_data)
        for cls in dart_classes
    ]
    if args.mods:
        # todo: factor this out pls
        by_mod = collections.defaultdict(list)
        for cls, exprs in zip(by_name.values(), gen_cls):
            by_mod[cls.__module__].append((cls, exprs))
        if args.output == '-':
            raise ValueError("can't use '-' with --mods")
        if os.path.exists(args.output) and not os.path.isdir(args.output):
            raise ValueError(f"output dir {args.output} isn't a directory")
        if not os.path.exists(args.output):
            os.makedirs(args.output)
        shutil.copy(os.path.join(os.path.dirname(__file__), 'jsonbase.dart'), args.output)
        for mod, pairs in by_mod.items():
            # sorting so subsequent runs produce consistent diffs; ideally sort by line number in orig source file
            pairs.sort(key=lambda pair: pair[0].__name__)
            fname = mod_out_path(args.output, mod)
            print('writing', fname)
            with open(fname, 'w') as outfile:
                write_preamble(outfile, local_imports(mod, (cls for cls, _ in pairs)))
                for _, exprs in pairs:
                    outfile.write('\n'.join(format_exprs(exprs.render())))
                    outfile.write('\n\n')
    else:
        outfile = sys.stdout if args.output == '-' else open(args.output, 'w')
        write_preamble(outfile)
        for exprs in gen_cls:
            # todo: python source file + line
            outfile.write('\n'.join(format_exprs(exprs.render())))
            outfile.write('\n\n')

def local_imports(current_module: str, classes: Sequence[pydantic.BaseModel]) -> List[str]:
    "return list of local import statements using dep_classes() to find dependencies"
    deps = {
        depcls.__module__
        for cls in classes
        for depcls in dep_classes(cls)
        if depcls.__module__ != current_module
    }
    return [
        f"import './{mod_out_path('', dep)}';"
        for dep in deps
    ]

def write_preamble(outfile, extras=()):
    lines = [
        '// generated by dartjsonclass (todo date + dunamai version)',
        "import 'dart:convert';",
        "import './jsonbase.dart';",
        *extras,
    ]
    outfile.write('\n'.join(lines) + '\n\n')

def mod_out_path(root: str, mod: str) -> str:
    "output path for module"
    return os.path.join(root, mod.split('.')[-1] + '.dart')


if __name__ == '__main__':
    main()
