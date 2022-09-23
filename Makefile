e2e:
	# generate classes + try compiling / running dart
	python -m dartjsonclass example.py > example.dart && dart main.dart
