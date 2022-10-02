lib/example.dart: example.py dartjsonclass/*.py
	python -m dartjsonclass example.py -o $@

e2e: lib/example.dart
	dart main.dart

dart-suite: lib/example.dart
	dart test

clean:
	rm -r .dart_tool/ .packages pubspec.lock
