lib/example.dart: example.py
	python -m dartjsonclass $< -o $@

e2e: lib/example.dart
	dart main.dart

dart-suite: lib/example.dart
	dart test -r expanded

clean:
	rm -r .dart_tool/ .packages pubspec.lock
