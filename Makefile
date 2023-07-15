lib/example.dart: example.py dartjsonclass/*.py
	python -m dartjsonclass example.py -o $@ --with-meta Msg Item StrList

e2e: lib/example.dart
	dart main.dart

dart-suite: lib/example.dart
	dart test

clean:
	rm -rf .dart_tool/ .packages pubspec.lock
