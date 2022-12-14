import 'package:djc_example/jsonbase.dart';
import 'package:djc_example/example.dart';
import 'package:test/test.dart';

/// convert to map and back to T
T mapRoundtrip<T extends JsonBaseMeta>(fromMap, T t) => fromMap(t.toMap());

/// convert to json and back to T
T jsonRoundtrip<T extends JsonBaseMeta>(fromJson, T t) => fromJson(t.toJson());

/// common tests for simple + complex classes
void commonTests<T extends JsonBaseMeta>(fromMap, fromJson, List<String> fields, T t) {
  test('roundtrip_equal', () {
    expect(t, mapRoundtrip(fromMap, t));
    expect(t, jsonRoundtrip(fromJson, t));
    expect(t.hashCode, jsonRoundtrip(fromJson, t).hashCode, reason: "hashCode");
  });

  test('copy_equal', () {
    expect(t, t.copy());
    expect(t.copy(), jsonRoundtrip(fromJson, t));
    expect(t.hashCode, t.copy().hashCode, reason: "hashCode");
  });
}

void main() {
  test('fromMap_null_field', () {
    expect(NullItem.fromMap({'item': null}), NullItem(null));
    expect(NullItem.fromMap({}), NullItem(null));
  });

  group('literal_collection', () {
    final strlist = StrList(["a", "b"], {"x": "y"});

    commonTests((x) => StrList.fromMap(x), (x) => StrList.fromJson(x), StrList.djc__fields, strlist);

    test('equality', () {
      expect(identical(strlist.strlist, strlist.copy().strlist), false);
      expect(strlist, strlist.copy());
    });

    test('fromMap', () {
      expect(strlist, mapRoundtrip((x) => StrList.fromMap(x), strlist));
      expect(strlist, jsonRoundtrip((x) => StrList.fromJson(x), strlist));
    });
  });

  final item = Item(1, "one");
  group('simple_Item', () {
    commonTests((x) => Item.fromMap(x), (x) => Item.fromJson(x), Item.djc__fields, item);

    test('value_equality', () {
      expect(item, item);
      expect(item, Item(1, "one"));
      expect(item == Item(1, "two"), false);
    });

    test('get_set', () {
      final item = Item(2, "two");
      expect(item.getAttr('a'), 2);
      item.setAttr('a', 3);
      expect(item.getAttr('a'), 3);
    });
  });

  group('complex_Msg', () {
    final msg = Msg(
      "12345",
      null,
      item,
      DateTime.parse("2022-01-01 12:00:00+00:00"),
      [Item(2, "two")],
      {"x": Item(3, "three")},
      {"y": Item(4, "four")},
    );

    commonTests((x) => Msg.fromMap(x), (x) => Msg.fromJson(x), Msg.djc__fields, msg);

    test('datetime', () {
      expect(msg.dt, TypeMatcher<DateTime>());
      final map = msg.toMap();
      expect(map['dt'], TypeMatcher<String>());
      final round = Msg.fromMap(map);
      expect(round.dt, msg.dt);
      expect(round.dt, TypeMatcher<DateTime>());
    });
  });

  test('unions', () {
    final msg = UnionTester(Item(1, "one"), [Item(0, "zero"), "string"], {"x": Item(3, "three"), "y": "string"});
    // note: because of dynamic fields from union, we're not testing for equality -- the Items in unions become toMap.
    // In this version of djc, we don't know how to rehydrate union types.
    final rt = UnionTester.fromJson(msg.toJson());
    expect(rt.list_union.length, 2);
    expect(rt.map_union.length, 2);
  });

  // todo: in deep copy, make sure collections, collection items, and JsonBase attrs are equal but not same instance
}
