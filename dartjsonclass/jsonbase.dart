// from dartjsonclass (package version)
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
