/// base class for json messages
abstract class JsonBase {
  Map<String, dynamic> toMap();

  toJson() {
    throw UnimplementedError("todo: use builtin json here");
  }
}
