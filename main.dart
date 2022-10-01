import './example.dart';

void main() {
  final item = Item(1, "one");
  print(item.toMap());
  print("toMap roundtrip:");
  print(Item.fromMap(item.toMap()).toMap());
  print("toJson:");
  print(item.toJson());
  print("json roundtrip:");
  final itemRound = Item.fromJson(item.toJson());
  print(itemRound.toMap());
  assert(item == item.copy());
  assert(item == itemRound);

  print('dataclass ==');
  print('yes ${item == item}, yes ${item == Item(1, "one")}, no ${item == Item(1, "two")}');

  final strlist = StrList(["a", "b"], {"x": "y"});
  print('strlist map roundtrip: ${StrList.fromMap(strlist.toMap()).toMap()}');
  print('strlist json roundtrip: ${StrList.fromJson(strlist.toJson()).toMap()}');

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
  final roundTrip = Msg.fromJson(msg.toJson());
  print(roundTrip.toMap());
  print('= roundtrip: ${msg == roundTrip}');
  assert(msg == roundTrip);
  print('getattr before ${msg.getAttr("maybe")}');
  msg.setAttr('maybe', 5);
  print('getattr after ${msg.getAttr("maybe")}');
  print('fields ${Msg.djc__fields.length} ${Msg.djc__fields}');
  print('hashCode ${msg.hashCode}');
}
