import './example.dart';

void main() {
  final item = Item(1, "one");
  print(item.toMap());
  print("toMap roundtrip:");
  print(Item.fromMap(item.toMap()).toMap());
  print("toJson:");
  print(item.toJson());
  print("json roundtrip:");
  print(Item.fromJson(item.toJson()).toMap());

  final msg = Msg(
    "12345",
    null,
    item,
    [Item(2, "two")],
    {"x": Item(3, "three")},
    {"y": Item(4, "four")},
  );
  print(msg.toMap());
  print("toMap roundtrip:");
  print(Msg.fromMap(msg.toMap()));
  print("toJson:");
  print(msg.toJson());
  print("json roundtrip:");
  print(Msg.fromJson(msg.toJson()).toMap());
}
