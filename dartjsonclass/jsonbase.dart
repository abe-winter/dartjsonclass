// from dartjsonclass (package version)
// todo: make json optional; from/to map is the more useful feature bc clients are doing their own serialization
import 'dart:convert';

/// base class for json messages
abstract class JsonBase<T> {
  Map<String, dynamic> toMap();

  String toJson() => jsonEncode(toMap());

  // dart why won't you love me
  // static JsonBase fromMap(Map<String, dynamic> map) => throw UnimplementedError("I'm abstract even though that's not allowed");
  // static JsonBase fromJson(String raw) => fromMap(jsonDecode(raw) as Map<String, dynamic>);

  // todo: --no-meta
  dynamic getAttr(String name);
  void setAttr(String name, dynamic val);

  T copy();
}

bool listEqual<T>(List<T>? a, List<T>? b, {bool Function(T?, T?)? pred}) {
  // this exists in flutter:collection, and seemingly *used to* exist in dart?
  // https://api.flutter.dev/flutter/dart.pkg.collection.equality/dart.pkg.collection.equality-library.html
  if (a == null || b == null) return a == b;
  if (a.length != b.length) return false;
  for (int i = 0; i < a.length; i++) {
    if (pred != null) {
      if (!pred(a[i], b[i])) return false;
    } else if (a[i] != b[i]) return false;
  }
  return true;
}

bool mapEqual<T>(Map<String, T>? a, Map<String, T>? b, {bool Function(T?, T?)? pred}) {
  if (a == null || b == null) return a == b;
  if (a.length != b.length) return false;
  for (final key in a.keys) {
    if (pred != null) {
      if (!pred(a[key], b[key])) return false;
    } else if (a[key] != b[key]) return false;
  }
  return true;
}
